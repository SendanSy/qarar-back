"""
Custom storage backends for AWS S3
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage backend for user-uploaded media files.
    Files are stored in the 'media/' directory in S3.
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'private'  # Media files are private by default
    
    def __init__(self, *args, **kwargs):
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