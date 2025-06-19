import pytest
from unittest.mock import patch, MagicMock
from django.core.paginator import Page
from django.test import RequestFactory

from .models import Review
from . import services
from .forms import ReviewForm


@pytest.fixture
def approved_reviews():
    """Pytest fixture to create a few approved reviews."""
    reviews = []
    for i in range(5):
        reviews.append(
            Review.objects.create(
                name=f"User {i}", email=f"user{i}@test.com", rating=i + 1,
                text=f"Test review {i}", approved=True
            )
        )
    return reviews


@pytest.mark.django_db
class TestReviewServices:
    """Tests for the review services."""

    def test_get_approved_reviews(self, approved_reviews):
        """Test getting paginated approved reviews."""
        page_obj, num_pages = services.get_approved_reviews(page=1, per_page=3)
        assert isinstance(page_obj, Page)
        assert len(page_obj.object_list) == 3
        assert num_pages == 2

    def test_create_review(self):
        """Test the create_review service function."""
        review = services.create_review(
            name="New Reviewer", email="new@test.com",
            rating=5, text="A brand new review."
        )
        assert review.approved is False
        assert Review.objects.count() == 1

    def test_get_review_statistics(self, approved_reviews):
        """Test the get_review_statistics service function."""
        stats = services.get_review_statistics()
        assert stats['total_reviews'] == 5
        assert stats['average_rating'] == 3.0  # (1+2+3+4+5)/5

    def test_handle_review_submission_valid(self):
        """Test handling a valid review form submission."""
        factory = RequestFactory()
        form_data = {
            'name': 'Good Reviewer', 'email': 'good@test.com',
            'rating': 5, 'text': 'This is a really good review.'
        }
        request = factory.post('/reviews/list/', form_data)
        
        with patch('apps.reviews.services.messages') as mock_messages:
            success, form = services.handle_review_submission(request)
            assert success is True
            assert form is None
            mock_messages.success.assert_called_once()
            assert Review.objects.count() == 1

    def test_handle_review_submission_invalid(self):
        """Test handling an invalid review form submission."""
        factory = RequestFactory()
        form_data = {'name': 'Bad', 'email': 'bad@test.com'}
        request = factory.post('/reviews/list/', form_data)
        
        with patch('apps.reviews.services.messages') as mock_messages:
            success, form = services.handle_review_submission(request)
            assert success is False
            assert isinstance(form, ReviewForm)
            assert mock_messages.error.call_count > 0

    def test_get_recent_reviews(self, approved_reviews):
        """Test fetching recent reviews."""
        # Create one unapproved review
        Review.objects.create(name="Unapproved", email="un@test.com", rating=1, text="...", approved=False)
        
        recent = services.get_recent_reviews(limit=3)
        assert len(recent) == 3
        assert all(r.approved for r in recent) 