import logging
from typing import Dict, Any, Optional

from django.http import HttpRequest, HttpResponse
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

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add form and pagination data to context."""
        context = super().get_context_data(**kwargs)

        form = kwargs.get('form', ReviewForm())
        context['form'] = form

        if context['paginator'] and context['page_obj']:
            pagination_context = services.get_pagination_context(context['page_obj'])
            context.update(pagination_context)

        context['stats'] = services.get_review_statistics()

        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
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

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add recent reviews to context."""
        context = super().get_context_data(**kwargs)

        context['is_widget'] = True

        context['recent_reviews'] = services.get_recent_reviews(limit=3)

        context['stats'] = services.get_review_statistics()

        return context
