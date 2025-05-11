import logging

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from .forms import ReviewForm
from .models import Review

logger = logging.getLogger(__name__)


class ReviewListView(ListView):
    """View for displaying the list of approved reviews with pagination."""
    model = Review
    template_name = 'reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        """Return only approved reviews ordered by creation date."""
        return Review.objects.filter(approved=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add form and pagination data to context."""
        context = super().get_context_data(**kwargs)
        context['form'] = ReviewForm()

        # Add pagination data to context
        if context['paginator'] and context['page_obj']:
            page_obj = context['page_obj']

            # Add pagination-related context
            context['current_page'] = page_obj.number
            context['total_pages'] = page_obj.paginator.num_pages
            context['has_previous'] = page_obj.has_previous()
            context['has_next'] = page_obj.has_next()

            # Add page range for pagination navigation
            page_range = []
            for i in range(max(1, page_obj.number - 2), min(page_obj.paginator.num_pages + 1, page_obj.number + 3)):
                page_range.append(i)
            context['page_range'] = page_range

        return context


class ReviewCreateView(CreateView):
    """View for creating a new review."""
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/form.html'
    success_url = reverse_lazy('reviews:list')

    def form_valid(self, form):
        """Process valid form data and add success message."""
        logger.info("ReviewCreateView: processing valid form")
        response = super().form_valid(form)
        messages.success(self.request, "Спасибо! Ваш отзыв отправлен и будет опубликован после модерации.")
        return response

    def form_invalid(self, form):
        """Handle invalid form data and show error messages."""
        logger.warning(f"ReviewCreateView: form validation failed - {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)
