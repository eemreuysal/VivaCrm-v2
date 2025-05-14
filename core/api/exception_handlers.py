"""
Custom exception handlers for Django REST Framework.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError, AuthenticationFailed, NotAuthenticated, 
    PermissionDenied, NotFound, MethodNotAllowed, Throttled
)
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides more detailed error responses.
    
    Args:
        exc: The exception that was raised
        context: The context of the exception
        
    Returns:
        Response: DRF Response object with error details
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    view = context.get('view', None)
    view_name = view.__class__.__name__ if view else 'Unknown'
    logger.error(
        f"Exception in {view_name}: {str(exc)}\n"
        f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
    )
    
    # If response is already handled by DRF, add additional info
    if response is not None:
        error_data = {
            'error': {
                'code': response.status_code,
                'message': get_error_message(exc),
                'detail': response.data,
                'type': exc.__class__.__name__
            }
        }
        
        if hasattr(exc, 'get_full_details'):
            error_data['error']['detail'] = exc.get_full_details()
        
        response.data = error_data
        return response
    
    # Handle Django's exceptions
    if isinstance(exc, Http404) or isinstance(exc, ObjectDoesNotExist):
        error_data = {
            'error': {
                'code': status.HTTP_404_NOT_FOUND,
                'message': 'Not found',
                'detail': str(exc),
                'type': exc.__class__.__name__
            }
        }
        return Response(error_data, status=status.HTTP_404_NOT_FOUND)
    
    # Handle any other unexpected exceptions
    if settings.DEBUG:
        error_data = {
            'error': {
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'Server error',
                'detail': str(exc),
                'type': exc.__class__.__name__,
                'traceback': traceback.format_exception(type(exc), exc, exc.__traceback__)
            }
        }
    else:
        # In production, don't expose traceback
        error_data = {
            'error': {
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'An unexpected error occurred',
                'type': 'ServerError'
            }
        }
    
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_error_message(exc):
    """
    Get a human-readable error message for common exceptions.
    
    Args:
        exc: The exception
        
    Returns:
        str: Human-readable error message
    """
    if isinstance(exc, ValidationError):
        return "Invalid input data"
    elif isinstance(exc, AuthenticationFailed):
        return "Authentication failed"
    elif isinstance(exc, NotAuthenticated):
        return "Authentication credentials were not provided"
    elif isinstance(exc, PermissionDenied):
        return "You do not have permission to perform this action"
    elif isinstance(exc, NotFound):
        return "The requested resource was not found"
    elif isinstance(exc, MethodNotAllowed):
        return f"Method {exc.args[0] if exc.args else ''} not allowed"
    elif isinstance(exc, Throttled):
        wait_time = exc.wait
        if wait_time:
            return f"Request was throttled. Try again in {wait_time} seconds."
        return "Request was throttled"
    
    return str(exc)