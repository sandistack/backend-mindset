"""
Development settings.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
# Menggunakan SQLite untuk development

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# CORS Settings - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# Email backend untuk development (console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Development-specific settings
INTERNAL_IPS = [
    '127.0.0.1',
]
