from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse

from . import services
from .forms import ReviewForm
from .models import Review


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

    def test_text_validation(self) -> None:
        """Test text field validation for minimum length."""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'rating': 5,
            'text': 'Short'  # Too short
        }
        form = ReviewForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_name_validation(self) -> None:
        """Test name field validation for minimum length."""
        data = {
            'name': 'T',  # Too short
            'email': 'test@example.com',
            'rating': 5,
            'text': 'This is a proper review text.'
        }
        form = ReviewForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ReviewServicesTest(TestCase):
    """Tests for the review services."""

    def setUp(self) -> None:
        for i in range(5):
            Review.objects.create(
                name=f"User {i}",
                email=f"user{i}@example.com",
                rating=5,
                text=f"Approved review {i}",
                approved=True
            )

        for i in range(3):
            Review.objects.create(
                name=f"Pending User {i}",
                email=f"pending{i}@example.com",
                rating=4,
                text=f"Unapproved review {i}",
                approved=False
            )

    def test_get_approved_reviews_queryset(self) -> None:
        """Test that the approved reviews queryset is filtered correctly."""
        queryset = services.get_approved_reviews_queryset()

        self.assertEqual(queryset.count(), 5)
        for review in queryset:
            self.assertTrue(review.approved)

    def test_get_approved_reviews(self) -> None:
        """Test that approved reviews are paginated correctly."""
        page_obj, total_pages = services.get_approved_reviews(page=1, per_page=3)

        self.assertEqual(len(page_obj), 3)  # 3 per page
        self.assertEqual(total_pages, 2)  # 5 total / 3 per page = 2 pages

    def test_create_review(self) -> None:
        """Test review creation."""
        review = services.create_review(
            name='New User',
            email='new@example.com',
            rating=4,
            text='New test review'
        )

        self.assertEqual(review.name, 'New User')
        self.assertEqual(review.email, 'new@example.com')
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.text, 'New test review')
        self.assertFalse(review.approved)
        self.assertEqual(Review.objects.count(), 9)

    def test_get_pagination_context(self) -> None:
        """Test generation of pagination context."""
        page_obj, _ = services.get_approved_reviews(page=1, per_page=2)
        context = services.get_pagination_context(page_obj)

        self.assertEqual(context['current_page'], 1)
        self.assertEqual(context['total_pages'], 3)
        self.assertFalse(context['has_previous'])
        self.assertTrue(context['has_next'])
        self.assertEqual(context['page_range'], [1, 2, 3])

    def test_handle_review_submission(self) -> None:
        """Test handling review form submission with valid and invalid data."""
        request = self.client.request().wsgi_request
        request.POST = {
            'name': 'Test User',
            'email': 'test@example.com',
            'rating': 5,
            'text': 'This is a valid review text'
        }

        success, form = services.handle_review_submission(request)
        self.assertTrue(success)
        self.assertIsNone(form)
        
        self.assertEqual(Review.objects.count(), 9)

        request.POST = {
            'name': 'Test User',
            'rating': 5,
            'text': 'This is a valid review text'
        }
        
        success, form = services.handle_review_submission(request)
        self.assertFalse(success)
        self.assertIsNotNone(form)
        self.assertIn('email', form.errors)

    def test_get_review_statistics(self) -> None:
        """Test getting review statistics."""
        stats = services.get_review_statistics()
        
        self.assertEqual(stats['total_reviews'], 5)
        self.assertEqual(stats['average_rating'], 5.0)
        self.assertEqual(len(stats['rating_percentages']), 5)
        self.assertEqual(stats['rating_percentages'][5], 100.0)

    def test_get_recent_reviews(self) -> None:
        """Test getting recent reviews."""
        reviews = services.get_recent_reviews(limit=2)
        
        self.assertEqual(len(reviews), 2)
        for review in reviews:
            self.assertTrue(review.approved)


class ReviewViewsTest(TestCase):
    """Tests for the review views."""

    def setUp(self) -> None:
        self.client = Client()

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
        self.assertEqual(len(response.context['reviews']), 3)
        
        self.assertEqual(response.context['form'].__class__, ReviewForm)
        self.assertIn('stats', response.context)

    def test_list_view_post(self) -> None:
        """Test the ReviewListView with POST request (submitting a review)."""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'rating': 5,
            'text': 'This is a test review that is long enough to pass validation'
        }

        response = self.client.post(reverse('reviews:list'), data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('reviews:list'))

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Спасибо!", str(messages[0]))

        self.assertEqual(Review.objects.count(), 4)
        self.assertEqual(Review.objects.filter(approved=False).count(), 1)

    def test_list_view_post_invalid(self) -> None:
        """Test the ReviewListView with invalid POST data."""
        data = {
            'name': 'Test User',
            'rating': 5
        }

        response = self.client.post(reverse('reviews:list'), data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/list.html')
        self.assertFalse(response.context['form'].is_valid())

        self.assertEqual(Review.objects.count(), 3)

    def test_widget_view(self) -> None:
        """Test the ReviewWidgetView."""
        response = self.client.get(reverse('reviews:widget'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/widget.html')
        self.assertIn('recent_reviews', response.context)
        self.assertIn('stats', response.context)
        self.assertEqual(len(response.context['recent_reviews']), 3)
