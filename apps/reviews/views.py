from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
import logging
import requests

from .models import Review
from .forms import ReviewForm

logger = logging.getLogger(__name__)

def review_list(request):
    """Display approved reviews with pagination"""
    reviews = Review.objects.filter(approved=True).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reviews, 20)  # 20 reviews per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Show form on the reviews page
    form = ReviewForm()
    
    context = {
        'page_obj': page_obj,
        'total_pages': paginator.num_pages,
        'form': form
    }
    
    return render(request, 'reviews/list.html', context)

def add_review(request):
    """Handle adding a new review"""
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Save the form but don't send notifications here (they're handled by signals)
            review = form.save()
            
            # Success message
            messages.success(request, "Спасибо! Ваш отзыв отправлен и будет опубликован после модерации.")
            return redirect('reviews:list')
        else:
            # If form is invalid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/form.html', {'form': form})
