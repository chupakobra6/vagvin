import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView

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
        
        # Use form from POST data if available (e.g., after failed validation)
        form = kwargs.get('form', ReviewForm())
        context['form'] = form

        # Add pagination data to context
        if context['paginator'] and context['page_obj']:
            pagination_context = services.get_pagination_context(context['page_obj'])
            context.update(pagination_context)

        return context
        
    def post(self, request, *args, **kwargs):
        """Handle review form submission."""
        form = ReviewForm(request.POST)
        
        if form.is_valid():
            try:
                services.create_review(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    rating=form.cleaned_data['rating'],
                    text=form.cleaned_data['text']
                )
                messages.success(request, "Спасибо! Ваш отзыв отправлен и будет опубликован после модерации.")
                return redirect('reviews:list')
            except Exception:
                logger.exception("Error saving review")
                messages.error(request, "Произошла ошибка при сохранении отзыва. Пожалуйста, попробуйте еще раз.")
                # Setup for rendering
                self.object_list = self.get_queryset()
                return self.render_to_response(self.get_context_data(form=form))
        else:
            logger.warning("Review form validation failed")
            
            # Add error messages without field prefixes
            for field_name, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, error)
            
            # Setup for rendering
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data(form=form))
