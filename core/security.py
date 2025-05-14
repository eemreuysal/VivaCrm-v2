"""
Security utilities and configurations for VivaCRM v2.

This module provides security-related functionality such as:
- Password validation and strength checking
- Content sanitization
- Security headers configuration
- Rate limiting functions
- CSRF token utilities
- Security middleware
"""
import bleach
import re
import string
from django.http import HttpRequest
from django.conf import settings
from typing import Dict, List, Optional, Any, Union, Callable
import logging

logger = logging.getLogger(__name__)

# Sanitization configuration
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code',
    'div', 'em', 'i', 'li', 'ol', 'p', 'span', 'strong', 'ul',
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel', 'target'],
    'abbr': ['title'],
    'acronym': ['title'],
    'div': ['class'],
    'p': ['class'],
    'span': ['class'],
}

# Regular expressions for various validation checks
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[\d\s\(\)-]{8,20}$')
URL_REGEX = re.compile(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(/[-\w./?%&=]*)?$')
TAX_ID_REGEX = re.compile(r'^\d{10,11}$')  # Turkish Tax ID format


def sanitize_html(content: str) -> str:
    """
    Sanitize HTML content to remove potentially dangerous tags and attributes.
    
    Args:
        content (str): HTML content to sanitize
        
    Returns:
        str: Sanitized HTML content
    """
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )


def sanitize_inputs(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize dictionary inputs, especially HTML fields.
    
    Args:
        data (dict): Dictionary containing user input data
        
    Returns:
        dict: Sanitized data dictionary
    """
    sanitized_data = {}
    text_fields = ['name', 'title', 'description', 'notes', 'content', 'address']
    html_fields = ['description_html', 'notes_html', 'content_html']
    
    for key, value in data.items():
        if value is None or not isinstance(value, str):
            sanitized_data[key] = value
            continue
            
        if key in html_fields:
            sanitized_data[key] = sanitize_html(value)
        elif key in text_fields:
            # For text fields, remove any HTML tags completely
            sanitized_data[key] = bleach.clean(value, tags=[], strip=True)
        else:
            # For other fields, keep as is but ensure they're strings
            sanitized_data[key] = str(value)
    
    return sanitized_data


def check_password_strength(password: str) -> Dict[str, Union[bool, List[str]]]:
    """
    Check password strength against multiple criteria.
    
    Args:
        password (str): Password to check
        
    Returns:
        dict: Dictionary with strength assessment and failure reasons
    """
    min_length = 8
    reasons = []
    
    # Check minimum length
    if len(password) < min_length:
        reasons.append(f"Password must be at least {min_length} characters long")
    
    # Check for uppercase letters
    if not any(c.isupper() for c in password):
        reasons.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letters
    if not any(c.islower() for c in password):
        reasons.append("Password must contain at least one lowercase letter")
    
    # Check for digits
    if not any(c.isdigit() for c in password):
        reasons.append("Password must contain at least one digit")
    
    # Check for special characters
    special_chars = set(string.punctuation)
    if not any(c in special_chars for c in password):
        reasons.append("Password must contain at least one special character")
    
    return {
        'is_strong': len(reasons) == 0,
        'reasons': reasons
    }


def get_secure_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP responses.
    
    Returns:
        dict: Dictionary mapping header names to values
    """
    is_development = settings.DEBUG
    
    headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'X-Frame-Options': 'SAMEORIGIN',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
    }
    
    # Only add CSP in production as it can interfere with development
    if not is_development:
        headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net https://unpkg.com; "
            "connect-src 'self'; "
            "frame-src 'self'; "
            "object-src 'none';"
        )
    
    return headers


class SecurityHeadersMiddleware:
    """
    Middleware for adding security headers to all responses.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        
        # Add security headers
        for header, value in get_secure_headers().items():
            response[header] = value
        
        return response


def log_security_event(event_type: str, description: str, user=None, ip_address=None, additional_data=None):
    """
    Log a security-related event.
    
    Args:
        event_type (str): Type of security event (e.g., 'login_failed', 'access_denied')
        description (str): Description of the event
        user: The user associated with the event, if any
        ip_address (str): IP address associated with the event
        additional_data (dict): Any additional data to log
    """
    try:
        log_data = {
            'event_type': event_type,
            'description': description,
            'user': str(user) if user else 'anonymous',
            'ip_address': ip_address,
            **(additional_data or {})
        }
        
        logger.warning(f"Security event: {log_data}")
        
        # If we have a security audit model, we could save it to the database here
        
    except Exception as e:
        logger.error(f"Error logging security event: {str(e)}")


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email))


def validate_phone(phone: str) -> bool:
    """
    Validate a phone number format.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
    return bool(PHONE_REGEX.match(phone))


def validate_url(url: str) -> bool:
    """
    Validate a URL format.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not url:
        return False
    return bool(URL_REGEX.match(url))


def validate_tax_id(tax_id: str) -> bool:
    """
    Validate a Turkish tax ID format.
    
    Args:
        tax_id (str): Tax ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not tax_id:
        return False
    return bool(TAX_ID_REGEX.match(tax_id))