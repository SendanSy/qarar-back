"""
Custom validators for the Qarar project.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.conf import settings


class ArabicTextValidator:
    """
    Validator to ensure text contains Arabic characters.
    """
    
    def __init__(self, min_ratio=0.1):
        self.min_ratio = min_ratio
    
    def __call__(self, value):
        if not value:
            return
        
        # Count Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', value))
        total_chars = len(re.sub(r'\s', '', value))
        
        if total_chars > 0:
            ratio = arabic_chars / total_chars
            if ratio < self.min_ratio:
                raise ValidationError(
                    _('Text must contain at least %(min_ratio)s%% Arabic characters.'),
                    params={'min_ratio': int(self.min_ratio * 100)},
                )


class SlugValidator(RegexValidator):
    """
    Validator for URL-friendly slugs.
    """
    regex = r'^[-a-zA-Z0-9_]+$'
    message = _('Enter a valid slug consisting of letters, numbers, underscores or hyphens.')
    flags = 0


class PhoneNumberValidator:
    """
    Validator for phone numbers (Syrian format).
    """
    
    def __call__(self, value):
        if not value:
            return
        
        # Remove all non-digit characters
        digits = re.sub(r'[^\d]', '', value)
        
        # Check for valid Syrian phone number patterns
        patterns = [
            r'^963\d{8,9}$',  # +963 followed by 8-9 digits
            r'^0\d{8,9}$',    # 0 followed by 8-9 digits
            r'^\d{8,9}$',     # 8-9 digits
        ]
        
        is_valid = any(re.match(pattern, digits) for pattern in patterns)
        
        if not is_valid:
            raise ValidationError(
                _('Enter a valid Syrian phone number.')
            )


class FileTypeValidator:
    """
    Validator for file types based on extension.
    """
    
    def __init__(self, allowed_extensions):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
    
    def __call__(self, value):
        if not value:
            return
        
        extension = value.name.split('.')[-1].lower()
        
        if extension not in self.allowed_extensions:
            raise ValidationError(
                _('File type not allowed. Allowed types: %(allowed_types)s'),
                params={'allowed_types': ', '.join(self.allowed_extensions)},
            )


class FileSizeValidator:
    """
    Validator for file size limits.
    """
    
    def __init__(self, max_size_mb):
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    def __call__(self, value):
        if not value:
            return
        
        if value.size > self.max_size_bytes:
            raise ValidationError(
                _('File size too large. Maximum size: %(max_size)sMB'),
                params={'max_size': self.max_size_mb},
            )


class ImageDimensionValidator:
    """
    Validator for image dimensions.
    """
    
    def __init__(self, max_width=None, max_height=None, min_width=None, min_height=None):
        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height
    
    def __call__(self, value):
        if not value:
            return
        
        try:
            from PIL import Image
            image = Image.open(value)
            width, height = image.size
            
            if self.max_width and width > self.max_width:
                raise ValidationError(
                    _('Image width too large. Maximum width: %(max_width)spx'),
                    params={'max_width': self.max_width},
                )
            
            if self.max_height and height > self.max_height:
                raise ValidationError(
                    _('Image height too large. Maximum height: %(max_height)spx'),
                    params={'max_height': self.max_height},
                )
            
            if self.min_width and width < self.min_width:
                raise ValidationError(
                    _('Image width too small. Minimum width: %(min_width)spx'),
                    params={'min_width': self.min_width},
                )
            
            if self.min_height and height < self.min_height:
                raise ValidationError(
                    _('Image height too small. Minimum height: %(min_height)spx'),
                    params={'min_height': self.min_height},
                )
        
        except Exception as e:
            raise ValidationError(_('Invalid image file.'))


class HashtagValidator:
    """
    Validator for hashtags.
    """
    
    def __call__(self, value):
        if not value:
            return
        
        # Remove # if present
        tag = value.lstrip('#')
        
        # Check format
        if not re.match(r'^[a-zA-Z0-9_\u0600-\u06FF]+$', tag):
            raise ValidationError(
                _('Hashtag must contain only letters, numbers, underscores, and Arabic characters.')
            )
        
        # Check length
        if len(tag) < 2:
            raise ValidationError(
                _('Hashtag must be at least 2 characters long.')
            )
        
        if len(tag) > 50:
            raise ValidationError(
                _('Hashtag must be less than 50 characters long.')
            )


class URLValidator:
    """
    Enhanced URL validator with additional checks.
    """
    
    def __init__(self, schemes=None, allowed_domains=None):
        self.schemes = schemes or ['http', 'https']
        self.allowed_domains = allowed_domains or []
    
    def __call__(self, value):
        if not value:
            return
        
        # Basic URL pattern
        url_pattern = re.compile(
            r'^(?:(?P<scheme>https?):\/\/)?'  # scheme
            r'(?:(?P<user>[^\s:@\/]+)(?::(?P<pass>[^\s:@\/]+))?@)?'  # user:pass@
            r'(?P<host>(?:[^\s:@\/]+\.)*[^\s:@\/]+)'  # host
            r'(?::(?P<port>\d+))?'  # port
            r'(?P<path>\/[^\s]*)?$'  # path
        )
        
        match = url_pattern.match(value)
        if not match:
            raise ValidationError(_('Enter a valid URL.'))
        
        scheme = match.group('scheme')
        host = match.group('host')
        
        # Check scheme
        if scheme and scheme not in self.schemes:
            raise ValidationError(
                _('URL scheme not allowed. Allowed schemes: %(schemes)s'),
                params={'schemes': ', '.join(self.schemes)},
            )
        
        # Check domain
        if self.allowed_domains and host not in self.allowed_domains:
            raise ValidationError(
                _('Domain not allowed. Allowed domains: %(domains)s'),
                params={'domains': ', '.join(self.allowed_domains)},
            )


class UsernameValidator:
    """
    Validator for usernames.
    """
    
    def __call__(self, value):
        if not value:
            return
        
        # Check format
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError(
                _('Username must contain only letters, numbers, and underscores.')
            )
        
        # Check length
        if len(value) < 3:
            raise ValidationError(
                _('Username must be at least 3 characters long.')
            )
        
        if len(value) > 30:
            raise ValidationError(
                _('Username must be less than 30 characters long.')
            )
        
        # Check for reserved usernames
        reserved_usernames = [
            'admin', 'administrator', 'root', 'system', 'api', 'www',
            'mail', 'email', 'support', 'help', 'news', 'info',
            'anonymous', 'guest', 'user', 'test', 'demo'
        ]
        
        if value.lower() in reserved_usernames:
            raise ValidationError(
                _('This username is reserved and cannot be used.')
            )


class PasswordStrengthValidator:
    """
    Validator for password strength.
    """
    
    def __init__(self, min_length=8, require_uppercase=True, require_lowercase=True, 
                 require_numbers=True, require_symbols=True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_symbols = require_symbols
    
    def __call__(self, value):
        if not value:
            return
        
        errors = []
        
        if len(value) < self.min_length:
            errors.append(
                _('Password must be at least %(min_length)d characters long.') % {
                    'min_length': self.min_length
                }
            )
        
        if self.require_uppercase and not re.search(r'[A-Z]', value):
            errors.append(_('Password must contain at least one uppercase letter.'))
        
        if self.require_lowercase and not re.search(r'[a-z]', value):
            errors.append(_('Password must contain at least one lowercase letter.'))
        
        if self.require_numbers and not re.search(r'\d', value):
            errors.append(_('Password must contain at least one number.'))
        
        if self.require_symbols and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            errors.append(_('Password must contain at least one special character.'))
        
        if errors:
            raise ValidationError(errors)


# Common validator instances
arabic_text_validator = ArabicTextValidator()
slug_validator = SlugValidator()
phone_number_validator = PhoneNumberValidator()
hashtag_validator = HashtagValidator()
username_validator = UsernameValidator()
password_strength_validator = PasswordStrengthValidator()

# File validators
image_file_validator = FileTypeValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])
document_file_validator = FileTypeValidator(['pdf', 'doc', 'docx', 'txt', 'rtf'])
profile_image_validator = FileSizeValidator(5)  # 5MB max
attachment_file_validator = FileSizeValidator(50)  # 50MB max

# Image dimension validators
avatar_image_validator = ImageDimensionValidator(max_width=500, max_height=500, min_width=50, min_height=50)
cover_image_validator = ImageDimensionValidator(max_width=1920, max_height=1080, min_width=400, min_height=200)