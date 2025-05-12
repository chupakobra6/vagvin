import logging.config
import os
from pathlib import Path

from django.utils.log import DEFAULT_LOGGING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Enable test mode for payments when in debug mode
PAYMENT_TEST_MODE = DEBUG

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Site URL
SITE_URL = os.environ.get('SITE_URL', 'https://vagvin.ru')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.pages.apps.PagesConfig',
    'apps.payments.apps.PaymentsConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.reports.apps.ReportsConfig',
    'apps.reviews.apps.ReviewsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vagvin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vagvin.wsgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": os.environ.get('CACHE_BACKEND', "django.core.cache.backends.locmem.LocMemCache"),
        "LOCATION": os.environ.get('CACHE_LOCATION', "vagvin-cache"),
        "TIMEOUT": int(os.environ.get('CACHE_TTL', 86400)),
    }
}

# Cache times (in seconds)
CACHE_TIME_SHORT = int(os.environ.get('CACHE_TIME_SHORT', 3600))  # 1 hour
CACHE_TIME_LONG = int(os.environ.get('CACHE_TIME_LONG', 86400))  # 24 hours

# Email configuration
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'VAGVIN <noreply@example.com>')

# Admin Email
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')

# Login URL and redirect settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'pages:home'

# Password reset settings
PASSWORD_RESET_TIMEOUT = 60 * 60 * 1  # 1 hour

# Session settings
SESSION_COOKIE_AGE = 60 * 60  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# API keys and external services
# Avito/Autoteka settings
AVITO_TOKEN_URL = os.environ.get('AVITO_TOKEN_URL', '')
AVITO_CLIENT_ID = os.environ.get('AVITO_CLIENT_ID', '')
AVITO_CLIENT_SECRET = os.environ.get('AVITO_CLIENT_SECRET', '')

# Carstat settings
CARSTAT_API_KEY = os.environ.get('CARSTAT_API_KEY', '')

# VINHistory settings
VINHISTORY_LOGIN = os.environ.get('VINHISTORY_LOGIN', '')
VINHISTORY_PASS = os.environ.get('VINHISTORY_PASS', '')

# Payment systems
# Robokassa settings
ROBOKASSA_LOGIN = os.environ.get('ROBOKASSA_LOGIN', '')
ROBOKASSA_PASSWORD1 = os.environ.get('ROBOKASSA_PASSWORD1', '')
ROBOKASSA_PASSWORD2 = os.environ.get('ROBOKASSA_PASSWORD2', '')
ALLOWED_ROBOKASSA_IPS = os.environ.get('ALLOWED_ROBOKASSA_IPS', '').split(',') if os.environ.get(
    'ALLOWED_ROBOKASSA_IPS') else []

# YooKassa settings
YOOKASSA_SHOP_ID = os.environ.get('YOOKASSA_SHOP_ID', '')
YOOKASSA_SECRET_KEY = os.environ.get('YOOKASSA_SECRET_KEY', '')
YOOKASSA_RETURN_URL = os.environ.get('YOOKASSA_RETURN_URL', 'https://vagvin.ru/payments/status/')

# Heleket settings
HELEKET_API_URL = os.environ.get('HELEKET_API_URL', 'https://api.heleket.com/v1/payment')
HELEKET_MERCHANT_ID = os.environ.get('HELEKET_MERCHANT_ID', '')
HELEKET_API_KEY = os.environ.get('HELEKET_API_KEY', '')
HELEKET_RETURN_URL = os.environ.get('HELEKET_RETURN_URL', 'https://vagvin.ru/payments/status/')
HELEKET_SUCCESS_URL = os.environ.get('HELEKET_SUCCESS_URL', 'https://vagvin.ru/payments/status/')
HELEKET_CALLBACK_URL = os.environ.get('HELEKET_CALLBACK_URL', 'https://vagvin.ru/payments/heleket/callback/')

# Set up logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/vagvin.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
