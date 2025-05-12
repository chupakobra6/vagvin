import logging

from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView

from . import services
from .forms import ReviewForm
from .models import Review

logger = logging.getLogger(__name__)


class ReviewListView(ListView):
    """View for displaying the list of approved reviews with pagination and handling new review submission."""
    model = Review
    template_name = 'reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        """Return only approved reviews ordered by creation date."""
        return services.get_approved_reviews_queryset()

    def get_context_data(self, **kwargs):
        """Add form and pagination data to context."""
        context = super().get_context_data(**kwargs)

        # Add review form
        form = kwargs.get('form', ReviewForm())
        context['form'] = form

        # Add pagination context
        if context['paginator'] and context['page_obj']:
            pagination_context = services.get_pagination_context(context['page_obj'])
            context.update(pagination_context)

        # Add review statistics
        context['stats'] = services.get_review_statistics()

        return context

    def post(self, request, *args, **kwargs):
        """Handle review form submission through the service layer."""
        success, form = services.handle_review_submission(request)

        if success:
            return redirect('reviews:list')
        else:
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data(form=form))


class ReviewWidgetView(TemplateView):
    """View for displaying a small widget of recent reviews."""
    template_name = 'reviews/list.html'

    def get_context_data(self, **kwargs):
        """Add recent reviews to context."""
        context = super().get_context_data(**kwargs)

        # Mark as widget display
        context['is_widget'] = True

        # Get recent reviews
        context['recent_reviews'] = services.get_recent_reviews(limit=3)

        # Add statistics
        context['stats'] = services.get_review_statistics()

        return context
