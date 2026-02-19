"""
Development settings for Senior Collaboration Platform.
"""

from .base import *

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Database - use local PostgreSQL in development
# Already configured in base.py, but can override here if needed

# Django Debug Toolbar (optional for development)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development CORS - allow all origins
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework - add browsable API in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Logging - more verbose in development
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Disable template caching in development (APP_DIRS already handles loaders)
# TEMPLATES[0]['OPTIONS']['loaders'] = [
#     'django.template.loaders.filesystem.Loader',
#     'django.template.loaders.app_directories.Loader',
# ]

# Show emails in console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

print("🚀 Running in DEVELOPMENT mode")
