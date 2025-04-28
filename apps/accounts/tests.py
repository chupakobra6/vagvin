import pytest
from decimal import Decimal
from typing import Dict, Any

from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from .models import User
from .services import UserService
from .payments import PaymentService

User = get_user_model()


@pytest.fixture
def test_user() -> User:
    """Create a test user"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    return user


@pytest.fixture
def authenticated_client(client: Client, test_user: User) -> Client:
    """Create an authenticated client"""
    client.login(username='testuser', password='testpassword123')
    return client


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model"""
    
    def test_create_user(self) -> None:
        """Test creating a user"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='password123'
        )
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.check_password('password123')
        assert user.referral_code is not None
        assert user.balance == 0
        assert user.overdraft == 0
    
    def test_referral_link(self, test_user: User) -> None:
        """Test user's referral link"""
        expected_link = reverse('accounts:register') + f"?ref={test_user.referral_code}"
        assert test_user.referral_link == expected_link
    
    def test_additional_emails(self, test_user: User) -> None:
        """Test additional emails functionality"""
        assert test_user.get_additional_emails() == []
        
        test_user.add_additional_email('second@example.com')
        assert test_user.get_additional_emails() == ['second@example.com']
        
        test_user.add_additional_email('third@example.com')
        assert set(test_user.get_additional_emails()) == {'second@example.com', 'third@example.com'}
        
        test_user.remove_additional_email('second@example.com')
        assert test_user.get_additional_emails() == ['third@example.com']


@pytest.mark.django_db
class TestUserService:
    """Tests for the UserService"""
    
    def test_authenticate_user(self, test_user: User) -> None:
        """Test authenticating a user"""
        user = UserService.authenticate_user('test@example.com', 'testpassword123')
        assert user is not None
        assert user.pk == test_user.pk
        
        # Test with wrong password
        user = UserService.authenticate_user('test@example.com', 'wrongpassword')
        assert user is None
        
        # Test with non-existent user
        user = UserService.authenticate_user('nonexistent@example.com', 'testpassword123')
        assert user is None
    
    def test_get_user_data(self, test_user: User) -> None:
        """Test getting user data"""
        # Add a referral
        referral = User.objects.create_user(
            username='referral',
            email='referral@example.com',
            password='password123',
            referral=test_user
        )
        
        # Add additional email
        test_user.add_additional_email('additional@example.com')
        
        data = UserService.get_user_data(test_user)
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
        assert data['balance'] == 0
        assert data['referral_code'] == test_user.referral_code
        assert data['additional_emails'] == ['additional@example.com']
        assert data['referrals_count'] == 1


@pytest.mark.django_db
class TestPaymentService:
    """Tests for the PaymentService"""
    
    def test_update_balance(self, test_user: User) -> None:
        """Test updating user balance"""
        # Add to balance
        success, data = PaymentService.update_balance(test_user, Decimal('100.00'))
        assert success is True
        assert data['new_balance'] == Decimal('100.00')
        
        # Check user's balance was updated
        test_user.refresh_from_db()
        assert test_user.balance == Decimal('100.00')
        
        # Subtract from balance
        success, data = PaymentService.update_balance(test_user, Decimal('-30.00'))
        assert success is True
        assert data['new_balance'] == Decimal('70.00')
        
        # Check user's balance was updated
        test_user.refresh_from_db()
        assert test_user.balance == Decimal('70.00')
    
    def test_can_afford(self, test_user: User) -> None:
        """Test checking if user can afford a payment"""
        # Set balance and overdraft
        test_user.balance = Decimal('50.00')
        test_user.overdraft = Decimal('20.00')
        test_user.save()
        
        # Test can afford (within balance)
        can_afford, _ = PaymentService.can_afford(test_user, Decimal('40.00'))
        assert can_afford is True
        
        # Test can afford (using overdraft)
        can_afford, _ = PaymentService.can_afford(test_user, Decimal('60.00'))
        assert can_afford is True
        
        # Test cannot afford
        can_afford, message = PaymentService.can_afford(test_user, Decimal('80.00'))
        assert can_afford is False
        assert "Insufficient funds" in message


@pytest.mark.django_db
class TestViews:
    """Tests for the views"""
    
    def test_login_view(self, client: Client, test_user: User) -> None:
        """Test login view"""
        url = reverse('accounts:login')
        
        # GET request should show the form
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context
        
        # POST with valid credentials should redirect to dashboard
        response = client.post(url, {
            'username': 'test@example.com',
            'password': 'testpassword123'
        })
        assert response.status_code == 302
        assert response.url == reverse('accounts:dashboard')
        
        # POST with invalid credentials should show error
        response = client.post(url, {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
    
    def test_dashboard_view(self, authenticated_client: Client, test_user: User) -> None:
        """Test dashboard view"""
        url = reverse('accounts:dashboard')
        
        # Authenticated user should see the dashboard
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'user_data' in response.context
        assert response.context['user_data']['username'] == 'testuser'
        
        # Unauthenticated user should be redirected to login
        unauthenticated_client = Client()
        response = unauthenticated_client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url 