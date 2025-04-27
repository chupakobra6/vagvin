from django.shortcuts import render


def home_view(request):
    return render(request, 'pages/home.html')


def about_view(request):
    return render(request, 'pages/about.html')


def faq_view(request):
    return render(request, 'pages/faq.html')


def requisites_view(request):
    return render(request, 'pages/requisites.html')


def examples_view(request):
    return render(request, 'pages/examples.html')


def reviews_view(request):
    return render(request, 'pages/reviews.html')


def login_view(request):
    return render(request, 'pages/login.html')


def privacy_policy_view(request):
    return render(request, 'pages/privacy_policy.html')


def payment_rules_view(request):
    return render(request, 'pages/payment_rules.html')
