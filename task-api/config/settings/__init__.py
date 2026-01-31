from decouple import config

env = config('DJANGO_ENV', default='development')

if env == 'production':
    from .production import *
    print("🚀 Running in PRODUCTION mode")
else:
    from .development import *
    print("🔧 Running in DEVELOPMENT mode")