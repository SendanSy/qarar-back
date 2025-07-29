"""
Custom storage backends for AWS S3
"""
import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage backend for user-uploaded media files.
    Files are stored in the 'media/' directory in S3.
    Can generate signed URLs based on configuration.
    """
    location = 'media'
    file_overwrite = False
    
    def __init__(self, *args, **kwargs):
        # Check if we should use signed URLs
        use_signed_urls = os.environ.get('AWS_USE_SIGNED_URLS', 'True').lower() == 'true'
        
        if use_signed_urls:
            # For signed URLs, use private ACL and S3 domain
            self.default_acl = 'private'
            self.querystring_auth = True
            self.querystring_expire = int(os.environ.get('AWS_SIGNED_URL_EXPIRE', '3600'))
            kwargs['custom_domain'] = False  # Use S3 domain for signed URLs
        else:
            # For public access, use public-read ACL and custom domain if available
            self.default_acl = 'public-read'
            self.querystring_auth = False
            kwargs['custom_domain'] = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
        
        super().__init__(*args, **kwargs)


class PublicMediaStorage(S3Boto3Storage):
    """
    Storage backend for public media files (like post images).
    Files are publicly accessible via URL.
    """
    location = 'media/public'
    file_overwrite = False
    default_acl = 'public-read'
    
    def __init__(self, *args, **kwargs):
        kwargs['custom_domain'] = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
        super().__init__(*args, **kwargs)


class PrivateMediaStorage(S3Boto3Storage):
    """
    Storage backend for private media files.
    Files require signed URLs for access.
    """
    location = 'media/private'
    file_overwrite = False
    default_acl = 'private'
    querystring_auth = True
    querystring_expire = 3600  # URLs expire after 1 hour
    
    def __init__(self, *args, **kwargs):
        kwargs['custom_domain'] = False  # Don't use CloudFront for private files
        super().__init__(*args, **kwargs)