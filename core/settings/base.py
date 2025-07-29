"""
Base settings for the Qarar project.
"""
import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured


def get_env_variable(var_name, default=None):
    """Get environment variable or raise exception."""
    value = os.environ.get(var_name, default)
    if value is None:
        raise ImproperlyConfigured(f"Environment variable {var_name} is not set")
    return value


def get_env_bool(var_name, default=False):
    """Get environment variable as boolean."""
    value = get_env_variable(var_name, str(default))
    return value.lower() in ('true', '1', 'yes', 'on')


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'admin_interface',
    'colorfield',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'taggit',
    'drf_yasg',
    'django_seed',
]

LOCAL_APPS = [
    'apps.core.apps.CoreConfig',
    'apps.users.apps.UsersConfig',
    'apps.content.apps.ContentConfig',
    'apps.geographics.apps.GeographicsConfig',
    'apps.producers.apps.ProducersConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Security settings
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': get_env_variable('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': get_env_variable('DB_NAME'),
        'USER': get_env_variable('DB_USER'),
        'PASSWORD': get_env_variable('DB_PASSWORD'),
        'HOST': get_env_variable('DB_HOST', 'localhost'),
        'PORT': get_env_variable('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 20,
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=int(get_env_variable('JWT_ACCESS_TOKEN_LIFETIME', '30'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(get_env_variable('JWT_REFRESH_TOKEN_LIFETIME', '90'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': get_env_variable('SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Email settings
EMAIL_BACKEND = get_env_variable('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = get_env_variable('EMAIL_HOST', '')
EMAIL_PORT = int(get_env_variable('EMAIL_PORT', '587'))
EMAIL_USE_TLS = get_env_bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = get_env_variable('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = get_env_variable('DEFAULT_FROM_EMAIL', 'noreply@qarar.com')

# Site configuration
SITE_URL = get_env_variable('SITE_URL', 'http://localhost:8000')

# Analytics settings
PAGE_VIEW_RETENTION_DAYS = int(get_env_variable('PAGE_VIEW_RETENTION_DAYS', '90'))
CONTENT_VIEW_RETENTION_DAYS = int(get_env_variable('CONTENT_VIEW_RETENTION_DAYS', '180'))
SEARCH_QUERY_RETENTION_DAYS = int(get_env_variable('SEARCH_QUERY_RETENTION_DAYS', '180'))
USER_ACTIVITY_RETENTION_DAYS = int(get_env_variable('USER_ACTIVITY_RETENTION_DAYS', '365'))

# Logging configuration
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Admin Interface
ADMIN_INTERFACE = {
    'TITLE': 'Qarar Administration',
    'HEADER': 'Qarar News Platform',
    'SHOW_THEMES': True,
    'THEMES': [
        {
            'TITLE': 'Default',
            'THEME': 'default',
            'ACTIVE': True,
        },
        {
            'TITLE': 'Dark',
            'THEME': 'dark',
            'ACTIVE': False,
        },
    ],
}

# Silenced system checks
SILENCED_SYSTEM_CHECKS = ['security.W019']