import logging

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect

from .forms import ReviewForm
from .models import Review

logger = logging.getLogger(__name__)


def review_list(request):
    reviews = Review.objects.filter(approved=True).order_by('-created_at')

    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    form = ReviewForm()

    context = {
        'page_obj': page_obj,
        'total_pages': paginator.num_pages,
        'form': form
    }

    return render(request, 'reviews/list.html', context)


def add_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Спасибо! Ваш отзыв отправлен и будет опубликован после модерации.")
            return redirect('reviews:list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ReviewForm()

    return render(request, 'reviews/form.html', {'form': form})
