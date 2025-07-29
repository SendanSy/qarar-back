"""
Staging settings for Qarar project.
"""
from .production import *

# Debug can be True in staging for testing
DEBUG = get_env_bool('DEBUG', False)

# Allowed hosts for staging
ALLOWED_HOSTS = get_env_variable('ALLOWED_HOSTS', 'staging.qarar.com').split(',')

# CORS settings for staging
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = get_env_variable('CORS_ALLOWED_ORIGINS', '').split(',')

# Less strict HTTPS settings for staging
SECURE_SSL_REDIRECT = get_env_bool('SECURE_SSL_REDIRECT', False)
SECURE_HSTS_SECONDS = 0 if not get_env_bool('SECURE_SSL_REDIRECT', False) else 31536000

# Email backend for staging (can use console for testing)
EMAIL_BACKEND = get_env_variable('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# Logging for staging
LOGGING['handlers']['console']['level'] = 'INFO'
LOGGING['loggers']['django']['level'] = 'INFO'