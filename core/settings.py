"""
DEPRECATED: This file is deprecated. Use core.settings package instead.
The settings are now split into environment-specific files:
- core.settings.base: Common settings
- core.settings.development: Development settings  
- core.settings.staging: Staging settings
- core.settings.production: Production settings

This file is kept for backward compatibility only.
"""

# Import from the new settings structure
from .settings import *
