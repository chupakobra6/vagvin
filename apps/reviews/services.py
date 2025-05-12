import logging
from typing import Dict, Any, Tuple, List, Optional

from django.core.paginator import Paginator, Page
from django.db.models import QuerySet, Count, Avg
from django.http import HttpRequest
from django.contrib import messages

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


def get_review_statistics() -> Dict[str, Any]:
    """
    Get review statistics.
    
    Returns:
        Dict containing review statistics (count, average rating)
    """
    try:
        stats = Review.objects.filter(approved=True).aggregate(
            count=Count('id'),
            avg_rating=Avg('rating')
        )
        
        return {
            'total_reviews': stats['count'] or 0,
            'average_rating': round(stats['avg_rating'] or 0, 1),
            'rating_percentages': get_rating_distribution()
        }
    except Exception:
        logger.exception("Failed to get review statistics")
        return {
            'total_reviews': 0,
            'average_rating': 0,
            'rating_percentages': {}
        }


def get_rating_distribution() -> Dict[int, float]:
    """
    Get percentage distribution of ratings.
    
    Returns:
        Dict with rating values as keys and percentage as values
    """
    try:
        total = Review.objects.filter(approved=True).count()
        if total == 0:
            return {i: 0 for i in range(1, 6)}
            
        distribution = {}
        for i in range(1, 6):
            count = Review.objects.filter(approved=True, rating=i).count()
            distribution[i] = round((count / total) * 100, 1) if total > 0 else 0
            
        return distribution
    except Exception:
        logger.exception("Failed to get rating distribution")
        return {i: 0 for i in range(1, 6)}


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


def handle_review_submission(request: HttpRequest) -> Tuple[bool, Optional[ReviewForm]]:
    """
    Handle review form submission.
    
    Args:
        request: HTTP request with POST data
        
    Returns:
        Tuple containing success status and form (if invalid)
    """
    form = ReviewForm(request.POST)

    if form.is_valid():
        try:
            create_review(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                rating=form.cleaned_data['rating'],
                text=form.cleaned_data['text']
            )
            messages.success(request, "Спасибо! Ваш отзыв отправлен и будет опубликован после модерации.")
            logger.info(f"Successfully submitted review from {form.cleaned_data['name']}")
            return True, None
        except Exception:
            logger.exception("Error saving review")
            messages.error(request, "Произошла ошибка при сохранении отзыва. Пожалуйста, попробуйте еще раз.")
            return False, form
    else:
        logger.warning(f"Review form validation failed: {form.errors}")
        
        for field_name, error_list in form.errors.items():
            for error in error_list:
                messages.error(request, error)
                
        return False, form


def get_recent_reviews(limit: int = 5) -> List[Review]:
    """
    Get most recent approved reviews.
    
    Args:
        limit: Maximum number of reviews to return
        
    Returns:
        List of recent review objects
    """
    try:
        return Review.objects.filter(approved=True).order_by('-created_at')[:limit]
    except Exception:
        logger.exception("Failed to get recent reviews")
        return []
