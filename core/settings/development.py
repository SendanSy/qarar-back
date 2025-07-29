"""
Development settings for Qarar project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable('SECRET_KEY', 'dev-secret-key-change-in-production')

# Allowed hosts for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Database settings for development (use PostgreSQL as configured in .env)
# DATABASES['default'].update({
#     'ENGINE': 'django.db.backends.sqlite3',
#     'NAME': BASE_DIR / 'db.sqlite3',
# })

# Development-specific apps
INSTALLED_APPS += [
    'debug_toolbar',
]

# Development middleware
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
]

# Debug toolbar configuration to avoid conflicts with API endpoints
def show_toolbar(request):
    """Custom callback to show toolbar only for non-API endpoints."""
    if not DEBUG:
        return False
    
    # Disable toolbar for API endpoints and documentation
    api_paths = ['/api/', '/swagger/', '/redoc/', '/__debug__/']
    if any(path in request.path for path in api_paths):
        return False
    
    # Check if request is from internal IP
    from django.conf import settings
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr and remote_addr in settings.INTERNAL_IPS:
        return True
    
    return False

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files settings for development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files settings for development
MEDIA_ROOT = BASE_DIR / 'media'

# Logging for development
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Remove file handler for development
if 'file' in LOGGING['handlers']:
    del LOGGING['handlers']['file']
    
# Update root logger to only use console
LOGGING['root']['handlers'] = ['console']

# Update django logger to only use console
LOGGING['loggers']['django']['handlers'] = ['console']

# Cache settings for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Development security settings (less strict)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False