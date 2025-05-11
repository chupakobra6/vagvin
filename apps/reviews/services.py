import logging
from typing import Any, Dict, Optional

from django.contrib import messages
from django.core.paginator import Paginator, Page
from django.http import HttpRequest

from .forms import ReviewForm
from .models import Review

logger = logging.getLogger(__name__)


class ReviewService:
    """Service class for handling review-related business logic."""

    @staticmethod
    def get_approved_reviews(page_number: int = 1, per_page: int = 10) -> tuple[Page, int]:
        """
        Get all approved reviews with pagination.
        
        Args:
            page_number: Current page number.
            per_page: Number of reviews per page.
            
        Returns:
            Tuple containing page object and total number of pages.
        """
        logger.info(f"Fetching approved reviews, page: {page_number}, items per page: {per_page}")
        reviews = Review.objects.filter(approved=True).order_by('-created_at')

        paginator = Paginator(reviews, per_page)
        page_obj = paginator.get_page(page_number)

        return page_obj, paginator.num_pages

    @staticmethod
    def create_review(form_data: Dict[str, Any]) -> tuple[bool, Optional[ReviewForm]]:
        """
        Create a new review from form data.
        
        Args:
            form_data: POST data from the review form.
            
        Returns:
            Tuple containing success status and form object (if validation failed).
        """
        form = ReviewForm(form_data)

        if form.is_valid():
            review = form.save()
            logger.info(f"New review created with ID: {review.id}")
            return True, None

        logger.warning(f"Review form validation failed: {form.errors}")
        return False, form

    @staticmethod
    def get_review_context(request: HttpRequest) -> Dict[str, Any]:
        """
        Get context for the review list page.
        
        Args:
            request: HTTP request object.
            
        Returns:
            Dictionary containing context data for the template.
        """
        page_number = request.GET.get('page', 1)
        page_obj, total_pages = ReviewService.get_approved_reviews(page_number=int(page_number))

        context = {
            'page_obj': page_obj,
            'total_pages': total_pages,
            'form': ReviewForm()
        }

        return context

    @staticmethod
    def process_review_form(request: HttpRequest) -> tuple[bool, Dict[str, Any]]:
        """
        Process the review form submission.
        
        Args:
            request: HTTP request object.
            
        Returns:
            Tuple containing success status and context for rendering.
        """
        success, form = ReviewService.create_review(request.POST)

        if success:
            messages.success(request, "Спасибо! Ваш отзыв отправлен и будет опубликован после модерации.")
            return True, {}

        # If form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

        return False, {'form': form}
