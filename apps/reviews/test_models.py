import pytest
from .models import Review


@pytest.mark.django_db
class TestReviewModel:
    """Tests for the Review model."""

    def test_review_creation_and_str(self):
        """Test that a review can be created and its string representation is correct."""
        review = Review.objects.create(
            name="John Doe",
            email="john@example.com",
            rating=4,
            text="This is a test review.",
        )
        assert review.name == "John Doe"
        assert review.rating == 4
        assert str(review) == "John Doe - 4★"
