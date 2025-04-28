import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# TODO: Валидировать наличие всех переменных окружения
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    # Django core libs
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party libs
    'rest_framework',
    # Local apps
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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vagvin.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site URL
SITE_URL = os.getenv('SITE_URL', 'https://vagvin.ru')

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Robokassa settings
ROBOKASSA_LOGIN = os.getenv('ROBOKASSA_LOGIN', '')
ROBOKASSA_PASSWORD1 = os.getenv('ROBOKASSA_PASSWORD1', '')
ROBOKASSA_PASSWORD2 = os.getenv('ROBOKASSA_PASSWORD2', '')
ALLOWED_ROBOKASSA_IPS = os.getenv('ALLOWED_ROBOKASSA_IPS', '').split(',') if os.getenv('ALLOWED_ROBOKASSA_IPS') else []

# YooKassa settings
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', '')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', '')
YOOKASSA_RETURN_URL = os.getenv('YOOKASSA_RETURN_URL', 'https://vagvin.ru/payments/status/')

# Heleket settings
HELEKET_API_URL = os.getenv('HELEKET_API_URL', 'https://api.heleket.com/v1/payment')
HELEKET_MERCHANT_ID = os.getenv('HELEKET_MERCHANT_ID', '')
HELEKET_API_KEY = os.getenv('HELEKET_API_KEY', '')
HELEKET_RETURN_URL = os.getenv('HELEKET_RETURN_URL', 'https://vagvin.ru/payments/status/')
HELEKET_SUCCESS_URL = os.getenv('HELEKET_SUCCESS_URL', 'https://vagvin.ru/payments/status/')
HELEKET_CALLBACK_URL = os.getenv('HELEKET_CALLBACK_URL', 'https://vagvin.ru/payments/heleket/callback/')

# Email configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'VAGVIN <noreply@vagvin.ru>')

# Admin Email
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')

# Login URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'pages:home'

# Password reset settings
PASSWORD_RESET_TIMEOUT = 60 * 60 * 1  # 1 hour

# Session settings
SESSION_COOKIE_AGE = 60 * 60  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# Avito/Autoteka settings
AVITO_TOKEN_URL = os.getenv('AVITO_TOKEN_URL')
AVITO_CLIENT_ID = os.getenv('AVITO_CLIENT_ID')
AVITO_CLIENT_SECRET = os.getenv('AVITO_CLIENT_SECRET')

# Carstat settings
CARSTAT_API_KEY = os.getenv('CARSTAT_API_KEY')

# VINHistory settings
VINHISTORY_LOGIN = os.getenv('VINHISTORY_LOGIN')
VINHISTORY_PASS = os.getenv('VINHISTORY_PASS')

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "vagvin-cache",
        "TIMEOUT": 86400,
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
            'formatter': 'verbose'
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
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
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
