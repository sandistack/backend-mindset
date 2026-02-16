"""
Settings initialization.
By default, use development settings. Override with DJANGO_SETTINGS_MODULE env variable.
"""
import os

# Default to development settings
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from .production import *
else:
    from .development import *
