import pytest
from .forms import ReviewForm


@pytest.mark.django_db
class TestReviewForm:
    """Tests for the ReviewForm."""

    def test_valid_form(self):
        """Test that the form is valid with correct data."""
        form_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "rating": 5,
            "text": "This is a valid review, long enough to pass validation.",
        }
        form = ReviewForm(data=form_data)
        assert form.is_valid()

    @pytest.mark.parametrize(
        "field, value, error_message",
        [
            ("name", "A", "Имя должно содержать минимум 2 символа."),
            ("text", "Short", "Текст отзыва должен содержать минимум 10 символов."),
            ("text", "a" * 1001, "Текст отзыва не должен превышать 1000 символов."),
        ],
    )
    def test_invalid_form(self, field, value, error_message):
        """Test form validation for various fields."""
        form_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "rating": 5,
            "text": "A default valid text for the review.",
        }
        form_data[field] = value
        form = ReviewForm(data=form_data)
        assert not form.is_valid()
        assert error_message in form.errors[field]

    def test_form_missing_fields(self):
        """Test that the form is invalid if required fields are missing."""
        form = ReviewForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "email" in form.errors
        assert "rating" in form.errors
        assert "text" in form.errors
