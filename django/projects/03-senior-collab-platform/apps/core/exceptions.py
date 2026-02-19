"""
Custom exception handler for consistent API error responses.
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.core.exceptions import PermissionDenied
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error response format.
    
    Response format:
    {
        "error": {
            "code": "error_code",
            "message": "Human-readable error message",
            "details": {...},  # Optional field-specific errors
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Now add custom error formatting
    if response is not None:
        custom_response_data = {
            'error': {
                'code': get_error_code(exc),
                'message': get_error_message(exc),
            }
        }
        
        # Add field-specific errors for validation errors
        if isinstance(exc, ValidationError):
            custom_response_data['error']['details'] = response.data
        
        # Log the error
        logger.error(
            f"API Error: {custom_response_data['error']['code']} - "
            f"{custom_response_data['error']['message']}"
        )
        
        response.data = custom_response_data
    
    return response


def get_error_code(exc):
    """Extract error code from exception"""
    if hasattr(exc, 'default_code'):
        return exc.default_code
    
    error_codes = {
        ValidationError: 'validation_error',
        PermissionDenied: 'permission_denied',
        Http404: 'not_found',
    }
    
    return error_codes.get(type(exc), 'server_error')


def get_error_message(exc):
    """Extract human-readable error message"""
    if isinstance(exc, ValidationError):
        return "Validation failed. Please check your input."
    
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Get first error message from dict
            return next(iter(exc.detail.values()))[0] if exc.detail else str(exc)
        return str(exc.detail)
    
    return str(exc)
