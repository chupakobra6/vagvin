from django.shortcuts import render

def home_view(request):
    """Home page view."""
    return render(request, 'pages/home.html')

def about_view(request):
    """About page view."""
    return render(request, 'pages/about.html')

def faq_view(request):
    """FAQ page view."""
    return render(request, 'pages/faq.html')

def requisites_view(request):
    return render(request, 'pages/requisites.html')

def examples_view(request):
    return render(request, 'pages/examples.html')

def reviews_view(request):
    return render(request, 'pages/reviews.html')

def login_view(request):
    return render(request, 'pages/login.html')
