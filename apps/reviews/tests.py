from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse

from .forms import ReviewForm
from .models import Review
from .services import ReviewService


class ReviewModelTest(TestCase):
    """Tests for the Review model."""

    def test_review_creation(self) -> None:
        """Test that a review can be created."""
        review = Review.objects.create(
            name="Test User",
            email="test@example.com",
            rating=5,
            text="This is a test review",
            approved=False
        )

        self.assertEqual(review.name, "Test User")
        self.assertEqual(review.email, "test@example.com")
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, "This is a test review")
        self.assertFalse(review.approved)

    def test_review_str_method(self) -> None:
        """Test the string representation of a review."""
        review = Review.objects.create(
            name="Test User",
            email="test@example.com",
            rating=5,
            text="This is a test review"
        )

        self.assertEqual(str(review), "Test User - 5★")


class ReviewFormTest(TestCase):
    """Tests for the ReviewForm."""

    def test_valid_form(self) -> None:
        """Test that the form is valid with proper data."""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'rating': 5,
            'text': 'This is a test review'
        }
        form = ReviewForm(data=data)

        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self) -> None:
        """Test that the form is invalid when missing required fields."""
        data = {'name': 'Test User'}
        form = ReviewForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('text', form.errors)


class ReviewServiceTest(TestCase):
    """Tests for the ReviewService."""

    def setUp(self) -> None:
        # Create approved reviews
        for i in range(5):
            Review.objects.create(
                name=f"User {i}",
                email=f"user{i}@example.com",
                rating=5,
                text=f"Approved review {i}",
                approved=True
            )

        # Create unapproved reviews
        for i in range(3):
            Review.objects.create(
                name=f"Pending User {i}",
                email=f"pending{i}@example.com",
                rating=4,
                text=f"Unapproved review {i}",
                approved=False
            )

    def test_get_approved_reviews(self) -> None:
        """Test that only approved reviews are retrieved."""
        page_obj, total_pages = ReviewService.get_approved_reviews()

        self.assertEqual(len(page_obj), 5)
        self.assertEqual(total_pages, 1)

    def test_create_review_valid_data(self) -> None:
        """Test review creation with valid data."""
        form_data = {
            'name': 'New User',
            'email': 'new@example.com',
            'rating': 4,
            'text': 'New test review'
        }

        success, form = ReviewService.create_review(form_data)

        self.assertTrue(success)
        self.assertIsNone(form)
        self.assertEqual(Review.objects.count(), 9)  # 5 approved + 3 unapproved + 1 new

    def test_create_review_invalid_data(self) -> None:
        """Test review creation with invalid data."""
        form_data = {
            'name': 'New User',
            # Missing email
            'rating': 4,
            'text': 'New test review'
        }

        success, form = ReviewService.create_review(form_data)

        self.assertFalse(success)
        self.assertIsNotNone(form)
        self.assertEqual(Review.objects.count(), 8)  # No new review created


class ReviewViewsTest(TestCase):
    """Tests for the review views."""

    def setUp(self) -> None:
        self.client = Client()

        # Create approved reviews
        for i in range(3):
            Review.objects.create(
                name=f"User {i}",
                email=f"user{i}@example.com",
                rating=5,
                text=f"Approved review {i}",
                approved=True
            )

    def test_list_view(self) -> None:
        """Test the ReviewListView."""
        response = self.client.get(reverse('reviews:list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/list.html')
        self.assertEqual(len(response.context['page_obj']), 3)
        self.assertIsInstance(response.context['form'], ReviewForm)

    def test_create_view_get(self) -> None:
        """Test the ReviewCreateView with GET request."""
        response = self.client.get(reverse('reviews:add'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/form.html')
        self.assertIsInstance(response.context['form'], ReviewForm)

    def test_create_view_post_valid(self) -> None:
        """Test the ReviewCreateView with valid POST data."""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'rating': 5,
            'text': 'This is a test review'
        }

        response = self.client.post(reverse('reviews:add'), data)

        self.assertEqual(response.status_code, 302)  # Redirect after successful submission
        self.assertRedirects(response, reverse('reviews:list'))

        # Check that a message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Спасибо!", str(messages[0]))

        # Check that a new review was created but not approved
        self.assertEqual(Review.objects.count(), 4)
        self.assertEqual(Review.objects.filter(approved=True).count(), 3)

    def test_create_view_post_invalid(self) -> None:
        """Test the ReviewCreateView with invalid POST data."""
        data = {
            'name': 'Test User',
            # Missing email and text
            'rating': 5
        }

        response = self.client.post(reverse('reviews:add'), data)

        self.assertEqual(response.status_code, 200)  # Form redisplayed
        self.assertTemplateUsed(response, 'reviews/form.html')
        self.assertFalse(response.context['form'].is_valid())

        # Check that no new review was created
        self.assertEqual(Review.objects.count(), 3)
