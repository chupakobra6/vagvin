import uuid
from decimal import Decimal

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from .models import Payment

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for generating test User instances"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpassword')


class PaymentFactory(DjangoModelFactory):
    """Factory for generating test Payment instances"""
    
    class Meta:
        model = Payment
    
    user = factory.SubFactory(UserFactory)
    provider = factory.Iterator(['robokassa', 'yookassa', 'heleket'])
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    
    @factory.lazy_attribute
    def total_amount(self):
        """Calculate total amount based on the provider"""
        commission_rates = {
            'robokassa': 0.1,
            'yookassa': 0.1,
            'heleket': 0.06,
        }
        rate = commission_rates.get(self.provider, 0.1)
        return round(float(self.amount) * (1 + rate), 2)
    
    @factory.lazy_attribute
    def invoice_id(self):
        """Generate unique invoice ID"""
        return f"{self.provider}_{uuid.uuid4().hex}"
    
    status = 'pending'


class SuccessfulPaymentFactory(PaymentFactory):
    """Factory for generating successful Payment instances"""
    status = 'success'


class FailedPaymentFactory(PaymentFactory):
    """Factory for generating failed Payment instances"""
    status = 'failed' 