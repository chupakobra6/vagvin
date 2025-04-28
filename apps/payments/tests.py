from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse

from .factories import PaymentFactory, SuccessfulPaymentFactory
from .models import Payment
from .services import (
    PaymentProcessor, RobokassaPaymentProcessor, 
    YookassaPaymentProcessor, HelekitPaymentProcessor,
    get_payment_processor
)
from .views import InitiateRobokassaPaymentView, RobokassaCallbackView

User = get_user_model()


class PaymentModelTestCase(TestCase):
    """Tests for the Payment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.payment = Payment.objects.create(
            user=self.user,
            provider='robokassa',
            amount=Decimal('100.00'),
            total_amount=Decimal('110.00'),
            invoice_id='test_123',
            status='pending'
        )
    
    def test_apply_commission(self):
        """Test the apply_commission method"""
        payment = Payment.objects.create(
            user=self.user,
            provider='robokassa',
            amount=Decimal('100.00'),
            total_amount=Decimal('0.00'),
            invoice_id='test_commission',
            status='pending'
        )
        
        result = payment.apply_commission(rate=0.15)
        self.assertEqual(result, Decimal('115.00'))
        self.assertEqual(payment.total_amount, Decimal('115.00'))
        
        result = payment.apply_commission(rate=0.2)
        self.assertEqual(result, Decimal('115.00'))
    
    def test_mark_as_successful(self):
        """Test marking a payment as successful"""
        self.payment.mark_as_successful()
        self.assertEqual(self.payment.status, 'success')
        self.assertTrue(self.payment.is_successful)
    
    def test_mark_as_failed(self):
        """Test marking a payment as failed"""
        self.payment.mark_as_failed()
        self.assertEqual(self.payment.status, 'failed')
        self.assertTrue(self.payment.is_failed)
    
    def test_commission_amount(self):
        """Test the commission_amount property"""
        self.assertEqual(self.payment.commission_amount, Decimal('10.00'))


class PaymentProcessorTestCase(TestCase):
    """Tests for the PaymentProcessor class"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.processor = PaymentProcessor('test_provider', 0.1)
    
    def test_generate_invoice_id(self):
        """Test generating invoice IDs"""
        invoice_id = self.processor.generate_invoice_id()
        self.assertTrue(invoice_id.startswith('test_provider_'))
        self.assertEqual(len(invoice_id), len('test_provider_') + 32)
    
    def test_calculate_total_amount(self):
        """Test calculating total amount with commission"""
        amount = Decimal('100.00')
        total = self.processor.calculate_total_amount(amount)
        self.assertEqual(total, Decimal('110.00'))
    
    def test_create_payment(self):
        """Test creating a payment"""
        amount = Decimal('100.00')
        payment = self.processor.create_payment(self.user, amount)
        
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.provider, 'test_provider')
        self.assertEqual(payment.amount, amount)
        self.assertEqual(payment.total_amount, Decimal('110.00'))
        self.assertTrue(payment.invoice_id.startswith('test_provider_'))
        self.assertEqual(payment.status, 'pending')


class RobokassaPaymentProcessorTestCase(TestCase):
    """Tests for the RobokassaPaymentProcessor"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.processor = RobokassaPaymentProcessor()
    
    def test_calculate_signature(self):
        """Test signature calculation"""
        signature = self.processor.calculate_signature('param1', 'param2', 'param3')
        self.assertEqual(len(signature), 32)
    
    @patch('apps.payments.services.settings')
    @patch('apps.payments.services.urlencode')
    def test_create_payment_url(self, mock_urlencode, mock_settings):
        """Test creating payment URL"""
        mock_settings.ROBOKASSA_LOGIN = 'test_login'
        mock_settings.ROBOKASSA_PASSWORD1 = 'test_password'
        mock_urlencode.return_value = 'encoded_params'
        
        payment = PaymentFactory(provider='robokassa')
        url = self.processor.create_payment_url(payment, self.user)
        
        self.assertEqual(url, 'https://auth.robokassa.ru/Merchant/Index.aspx?encoded_params')
        mock_urlencode.assert_called_once()


class GetPaymentProcessorTestCase(TestCase):
    """Tests for the get_payment_processor factory function"""
    
    def test_get_robokassa_processor(self):
        """Test getting Robokassa processor"""
        processor = get_payment_processor('robokassa')
        self.assertIsInstance(processor, RobokassaPaymentProcessor)
    
    def test_get_yookassa_processor(self):
        """Test getting YooKassa processor"""
        processor = get_payment_processor('yookassa')
        self.assertIsInstance(processor, YookassaPaymentProcessor)
    
    def test_get_heleket_processor(self):
        """Test getting Heleket processor"""
        processor = get_payment_processor('heleket')
        self.assertIsInstance(processor, HelekitPaymentProcessor)
    
    def test_get_invalid_processor(self):
        """Test getting invalid processor raises ValueError"""
        with self.assertRaises(ValueError):
            get_payment_processor('invalid_provider')


class PaymentViewsTestCase(TestCase):
    """Tests for the payment views"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
    
    @patch('apps.payments.views.create_robokassa_payment')
    def test_initiate_robokassa_payment(self, mock_create_payment):
        """Test initiating Robokassa payment"""
        payment = PaymentFactory(provider='robokassa')
        mock_create_payment.return_value = (payment, 'https://test.url')
        
        url = reverse('payments:robokassa_initiate')
        request = self.factory.post(
            url, 
            data={'amount': '100.00'},
            content_type='application/json'
        )
        request.user = self.user
        
        view = InitiateRobokassaPaymentView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {
                'success': True,
                'payment_url': 'https://test.url',
                'payment_id': payment.id
            }
        )
    
    @patch('apps.payments.views.verify_robokassa_callback')
    @patch('apps.payments.views.settings')
    def test_robokassa_callback(self, mock_settings, mock_verify_callback):
        """Test Robokassa callback handling"""
        payment = SuccessfulPaymentFactory(provider='robokassa')
        mock_settings.ALLOWED_ROBOKASSA_IPS = ['127.0.0.1']
        mock_verify_callback.return_value = (payment, True)
        
        url = reverse('payments:robokassa_callback')
        request = self.factory.get(url)
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        view = RobokassaCallbackView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), f"OK{payment.id}")
        mock_verify_callback.assert_called_once() 