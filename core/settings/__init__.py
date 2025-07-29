"""
Django settings initialization.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Determine which settings to use based on environment
# First check CURRENT_ENVIRONMENT, then fall back to DJANGO_ENV for backward compatibility
environment = os.environ.get('CURRENT_ENVIRONMENT', os.environ.get('DJANGO_ENV', 'development'))

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
else:
    from .development import *