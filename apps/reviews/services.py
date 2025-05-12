import logging
from typing import Dict, Any, Tuple

from django.core.paginator import Paginator, Page
from django.db.models import QuerySet

from .forms import ReviewForm
from .models import Review

logger = logging.getLogger(__name__)


def get_approved_reviews_queryset() -> QuerySet:
    """
    Get the queryset of approved reviews ordered by creation date.
    
    Returns:
        QuerySet: Filtered queryset of approved reviews
    """
    return Review.objects.filter(approved=True).order_by('-created_at')


def get_approved_reviews(*, page: int = 1, per_page: int = 10) -> Tuple[Page, int]:
    """
    Get paginated approved reviews.
    
    Args:
        page: Current page number
        per_page: Number of reviews per page
        
    Returns:
        Tuple containing a page object and total number of pages
    """
    logger.info(f"Getting approved reviews for page {page} with {per_page} items per page")
    reviews = get_approved_reviews_queryset()

    paginator = Paginator(reviews, per_page)
    page_obj = paginator.get_page(page)

    return page_obj, paginator.num_pages


def create_review(*, name: str, email: str, rating: int, text: str) -> Review:
    """
    Create a new review.
    
    Args:
        name: Reviewer's name
        email: Reviewer's email
        rating: Review rating (1-5)
        text: Review text content
        
    Returns:
        Review: The created review instance
    """
    try:
        review = Review.objects.create(
            name=name,
            email=email,
            rating=rating,
            text=text,
            approved=False
        )
        logger.info(f"Created new review from {name} with ID {review.id}")
        return review
    except Exception:
        logger.exception("Failed to create review")
        raise


def get_pagination_context(page_obj: Page) -> Dict[str, Any]:
    """
    Generate pagination context for templates.
    
    Args:
        page_obj: Django Page object
        
    Returns:
        Dict containing pagination context variables
    """
    page_range = []
    for i in range(
            max(1, page_obj.number - 2),
            min(page_obj.paginator.num_pages + 1, page_obj.number + 3)
    ):
        page_range.append(i)

    return {
        'current_page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'page_range': page_range,
    }


def validate_review_form(form_data: Dict[str, Any]) -> Tuple[bool, ReviewForm | None, Review | None]:
    """
    Validate review form data.
    
    Args:
        form_data: POST data from the review form
        
    Returns:
        Tuple containing: success status, form object (if invalid), created review (if valid)
    """
    form = ReviewForm(form_data)

    if form.is_valid():
        try:
            review = create_review(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                rating=form.cleaned_data['rating'],
                text=form.cleaned_data['text']
            )
            return True, None, review
        except Exception:
            logger.exception("Failed to save valid review form")
            return False, form, None

    logger.warning(f"Review form validation failed: {form.errors}")
    return False, form, None
