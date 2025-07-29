"""
Custom exceptions and error handling for the Qarar project.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class QararException(Exception):
    """
    Base exception class for Qarar application.
    """
    default_message = _('An error occurred')
    default_code = 'error'
    
    def __init__(self, message=None, code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class BusinessLogicError(QararException):
    """
    Exception for business logic violations.
    """
    default_message = _('Business logic error')
    default_code = 'business_logic_error'


class ValidationError(QararException):
    """
    Exception for validation errors.
    """
    default_message = _('Validation error')
    default_code = 'validation_error'


class PermissionDeniedError(QararException):
    """
    Exception for permission denied errors.
    """
    default_message = _('Permission denied')
    default_code = 'permission_denied'


class NotFoundError(QararException):
    """
    Exception for not found errors.
    """
    default_message = _('Resource not found')
    default_code = 'not_found'


class ConflictError(QararException):
    """
    Exception for conflict errors.
    """
    default_message = _('Conflict occurred')
    default_code = 'conflict'


class RateLimitError(QararException):
    """
    Exception for rate limit errors.
    """
    default_message = _('Rate limit exceeded')
    default_code = 'rate_limit_exceeded'


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Create a custom response for our custom exceptions
    if isinstance(exc, QararException):
        custom_response_data = {
            'error': {
                'code': exc.code,
                'message': str(exc.message),
                'details': exc.details,
            },
            'success': False,
        }
        
        # Map custom exceptions to HTTP status codes
        status_code_mapping = {
            'business_logic_error': status.HTTP_400_BAD_REQUEST,
            'validation_error': status.HTTP_400_BAD_REQUEST,
            'permission_denied': status.HTTP_403_FORBIDDEN,
            'not_found': status.HTTP_404_NOT_FOUND,
            'conflict': status.HTTP_409_CONFLICT,
            'rate_limit_exceeded': status.HTTP_429_TOO_MANY_REQUESTS,
        }
        
        status_code = status_code_mapping.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        response = Response(custom_response_data, status=status_code)
    
    # Handle Django's built-in exceptions
    elif isinstance(exc, Http404):
        custom_response_data = {
            'error': {
                'code': 'not_found',
                'message': _('The requested resource was not found.'),
                'details': {},
            },
            'success': False,
        }
        response = Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
    
    elif isinstance(exc, ValidationError):
        custom_response_data = {
            'error': {
                'code': 'validation_error',
                'message': _('Validation failed.'),
                'details': exc.message_dict if hasattr(exc, 'message_dict') else {'non_field_errors': [str(exc)]},
            },
            'success': False,
        }
        response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # If we have a response, customize it
    if response is not None:
        # Log the error
        logger.error(f"API Error: {exc}", exc_info=True, extra={
            'request': context.get('request'),
            'view': context.get('view'),
        })
        
        # Ensure consistent response format
        if not isinstance(response.data, dict) or 'error' not in response.data:
            custom_response_data = {
                'error': {
                    'code': 'api_error',
                    'message': _('An error occurred processing your request.'),
                    'details': response.data if isinstance(response.data, dict) else {},
                },
                'success': False,
            }
            response.data = custom_response_data
    
    return response


class APIResponse:
    """
    Utility class for creating consistent API responses.
    """
    
    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        """
        Create a successful API response.
        """
        response_data = {
            'success': True,
            'data': data,
        }
        
        if message:
            response_data['message'] = message
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message, code='error', details=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Create an error API response.
        """
        response_data = {
            'success': False,
            'error': {
                'code': code,
                'message': message,
                'details': details or {},
            },
        }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def created(data=None, message=None):
        """
        Create a resource created response.
        """
        return APIResponse.success(data, message, status.HTTP_201_CREATED)
    
    @staticmethod
    def no_content(message=None):
        """
        Create a no content response.
        """
        return APIResponse.success(None, message, status.HTTP_204_NO_CONTENT)
    
    @staticmethod
    def not_found(message=None):
        """
        Create a not found response.
        """
        return APIResponse.error(
            message or _('Resource not found'),
            'not_found',
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def permission_denied(message=None):
        """
        Create a permission denied response.
        """
        return APIResponse.error(
            message or _('Permission denied'),
            'permission_denied',
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def validation_error(details, message=None):
        """
        Create a validation error response.
        """
        return APIResponse.error(
            message or _('Validation failed'),
            'validation_error',
            details,
            status.HTTP_400_BAD_REQUEST
        )