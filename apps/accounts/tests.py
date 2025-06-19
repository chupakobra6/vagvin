import pytest
from django.urls import reverse
from django.test import Client
from .factories import UserFactory
from django.utils import timezone
from django.conf import settings
from unittest.mock import patch
from apps.accounts.services import UserService
from apps.accounts.models import User


@pytest.mark.django_db
class TestAccountsViews:
    def test_login_view(self):
        """Test user login."""
        user = UserFactory(password="password123")
        client = Client()

        # Use email for login as per the form
        login_data = {
            "username": user.email,  # LoginForm uses 'username' field for email
            "password": "password123",
        }

        response = client.post(reverse("accounts:login"), login_data)

        # After successful login, it should redirect to dashboard
        assert response.status_code == 302
        assert response.url == reverse("accounts:dashboard")

    def test_dashboard_unauthenticated(self):
        """Test that dashboard redirects unauthenticated users."""
        client = Client()
        response = client.get(reverse("accounts:dashboard"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
class TestUserService:

    def test_register_user_success(self):
        """Test successful user registration."""
        with patch(
            "apps.accounts.services.EmailService.send_registration_email"
        ) as mock_send_email:
            mock_send_email.return_value = True
            success, message, user = UserService.register_user("newuser@example.com")

            assert success is True
            assert user is not None
            assert user.email == "newuser@example.com"
            assert User.objects.filter(email="newuser@example.com").exists()
            mock_send_email.assert_called_once()

    def test_register_user_with_referral(self):
        """Test user registration with a referral code."""
        referrer = UserFactory()
        with patch(
            "apps.accounts.services.EmailService.send_registration_email"
        ) as mock_send_email:
            mock_send_email.return_value = True
            success, message, new_user = UserService.register_user(
                "ref_user@example.com", referrer.referral_code
            )

            assert success is True
            assert new_user is not None
            new_user.refresh_from_db()
            assert new_user.referral == referrer

    def test_register_user_existing(self):
        """Test registration with an existing email."""
        UserFactory(email="existing@example.com", username="existing")
        success, message, user = UserService.register_user("existing@example.com")
        assert success is False
        assert user is None
        assert "уже существует" in message

    def test_reset_password_success(self):
        """Test successful password reset."""
        user = UserFactory(email="reset@example.com")
        with patch(
            "apps.accounts.services.EmailService.send_password_reset_email"
        ) as mock_send_email:
            mock_send_email.return_value = True
            success, message = UserService.reset_password(user.email)
            assert success is True
            assert "Новый пароль был создан" in message
            mock_send_email.assert_called_once()

    def test_reset_password_too_soon(self):
        """Test password reset restriction within timeout period."""
        user = UserFactory(
            email="reset_soon@example.com", last_password_reset=timezone.now()
        )
        # Simulate that PASSWORD_RESET_TIMEOUT is 600 seconds
        settings.PASSWORD_RESET_TIMEOUT = 600
        success, message = UserService.reset_password(user.email)
        assert success is False
        assert "Подождите ещё" in message

    def test_add_remove_additional_email(self):
        """Test adding and removing an additional email."""
        user = UserFactory()

        # Add email
        success, msg, emails = UserService.add_additional_email(
            user, "add1@example.com"
        )
        assert success is True
        assert "add1@example.com" in emails
        user.refresh_from_db()
        assert "add1@example.com" in user.additional_emails

        # Remove email
        success, msg, emails = UserService.remove_additional_email(
            user, "add1@example.com"
        )
        assert success is True
        assert "add1@example.com" not in emails
        user.refresh_from_db()
        assert "add1@example.com" not in user.additional_emails


@pytest.mark.django_db
class TestAuthViews:

    @pytest.fixture
    def client(self):
        return Client()

    def test_register_view_get(self, client):
        """Test GET request on registration page."""
        response = client.get(reverse("accounts:register"))
        assert response.status_code == 200
        assert "form" in response.context

    @patch("apps.accounts.services.UserService.register_user")
    def test_register_view_post_success(self, mock_register, client):
        """Test successful POST request on registration page."""
        mock_register.return_value = (True, "Success message", None)
        form_data = {"email": "test@example.com"}

        response = client.post(reverse("accounts:register"), form_data)

        # On success, it redirects to the success_url defined in the view
        assert response.status_code == 302
        assert response.url == "/accounts/login/"
        mock_register.assert_called_once_with("test@example.com", None)

    @patch("apps.accounts.services.UserService.reset_password")
    def test_forgot_password_view_post_success(self, mock_reset, client):
        """Test successful POST on forgot password page."""
        mock_reset.return_value = (True, "Success message")
        form_data = {"email": "test@example.com"}

        response = client.post(reverse("accounts:forgot_password"), form_data)

        assert response.status_code == 302
        assert response.url == reverse("accounts:login")
        mock_reset.assert_called_once_with("test@example.com")

    def test_logout_view(self, client):
        """Test that logout redirects to home page."""
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("accounts:logout"))
        assert response.status_code == 302
        assert response.url == reverse("pages:home")
