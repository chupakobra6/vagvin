import pytest
from django.urls import reverse
from django.test import Client

from .models import Review


@pytest.fixture
def client():
    """Pytest fixture for Django test client."""
    return Client()


@pytest.fixture
def approved_review():
    """Pytest fixture for a single approved review."""
    return Review.objects.create(
        name="Test User", email="test@example.com", rating=5,
        text="A great service!", approved=True
    )


@pytest.mark.django_db
class TestReviewViews:
    """Tests for the review views."""

    def test_review_list_view_get(self, client, approved_review):
        """Test the GET request for the review list view."""
        response = client.get(reverse('reviews:list'))
        assert response.status_code == 200
        assert 'reviews/list.html' in (t.name for t in response.templates)
        assert approved_review in response.context['reviews']

    def test_review_list_view_post_valid(self, client):
        """Test a valid POST request to submit a review."""
        form_data = {
            'name': 'Jane Doe', 'email': 'jane@example.com',
            'rating': 5, 'text': 'This is an excellent review.'
        }
        response = client.post(reverse('reviews:list'), form_data, follow=True)
        assert response.status_code == 200
        assert 'messages' in response.context
        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert "Спасибо! Ваш отзыв отправлен" in str(messages[0])
        assert Review.objects.filter(email='jane@example.com').exists()

    def test_review_list_view_post_invalid(self, client):
        """Test an invalid POST request to submit a review."""
        form_data = {'name': 'J'}  # Invalid name
        response = client.post(reverse('reviews:list'), form_data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
        assert not Review.objects.exists()

    def test_review_widget_view(self, client, approved_review):
        """Test the review widget view."""
        response = client.get(reverse('reviews:widget'))
        assert response.status_code == 200
        assert 'reviews/list.html' in (t.name for t in response.templates)
        assert response.context['is_widget'] is True
        assert approved_review in response.context['recent_reviews'] 