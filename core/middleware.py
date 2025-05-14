"""
Middleware classes for VivaCRM v2.

Includes security, performance, monitoring, and logging middlewares.
"""
import logging
import re
import time
import json
from django.utils import timezone
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.urls import resolve, Resolver404
from core.query_optimizer import QueryCountMiddleware
from core.logging_filters import TraceIdMiddleware, get_current_trace_id

User = get_user_model()
logger = logging.getLogger(__name__)


class SecurityAuditMiddleware:
    """
    Middleware for logging security-relevant actions.
    """
    # Sensitive URL patterns that should be logged
    SENSITIVE_PATTERNS = [
        re.compile(r'^/accounts/login'),
        re.compile(r'^/accounts/logout'),
        re.compile(r'^/accounts/password_reset'),
        re.compile(r'^/admin/'),
        re.compile(r'^/api/token'),
        re.compile(r'^/api/accounts/'),
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        self._log_sensitive_request(request)
        
        # Get response
        response = self.get_response(request)
        
        # Process response
        self._log_sensitive_response(request, response)
        
        return response
    
    def _is_sensitive_url(self, path):
        """Check if the URL path matches sensitive patterns."""
        return any(pattern.match(path) for pattern in self.SENSITIVE_PATTERNS)
    
    def _log_sensitive_request(self, request):
        """Log sensitive requests."""
        if not self._is_sensitive_url(request.path):
            return
        
        # Get basic request information
        user_id = getattr(request.user, 'id', None)
        username = getattr(request.user, 'username', 'anonymous')
        
        # Log the request
        logger.info(
            f"Security audit: {request.method} request to {request.path} "
            f"by user {username} (ID: {user_id}) from IP {self._get_client_ip(request)}"
        )
    
    def _log_sensitive_response(self, request, response):
        """Log responses to sensitive requests."""
        if not self._is_sensitive_url(request.path):
            return
        
        # Log authentication failures
        if (request.path.startswith('/accounts/login') and 
            request.method == 'POST' and 
            response.status_code != 302):  # Not a redirect, which would indicate success
            logger.warning(
                f"Authentication failure at {request.path} "
                f"from IP {self._get_client_ip(request)}"
            )
    
    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get leftmost IP in the chain (client's IP)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor request/response times and log slow responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0)  # seconds
    
    def __call__(self, request):
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate response time
        duration = time.time() - start_time
        
        # Log slow responses
        if duration > self.slow_threshold:
            try:
                view_func = resolve(request.path).func.__name__
            except Resolver404:
                view_func = "unknown"
                
            logger.warning(
                f"Slow response detected: {request.method} {request.path} "
                f"took {duration:.2f}s to process. View: {view_func}. "
                f"User: {getattr(request.user, 'username', 'anonymous')}"
            )
        
        # Add timing header for API responses
        if request.path.startswith('/api/'):
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


class SQLQueryCountMiddleware:
    """
    Middleware to log number of SQL queries per request in development.
    Useful for identifying N+1 query problems.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only activate in DEBUG mode
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Import here to avoid importing in production
        from django.db import connection
        
        # Get initial query count
        initial_query_count = len(connection.queries)
        
        # Process request
        response = self.get_response(request)
        
        # Calculate total queries
        total_query_count = len(connection.queries) - initial_query_count
        
        # Log if query count is high
        if total_query_count > 50:  # Arbitrary threshold
            logger.warning(
                f"High query count: {request.method} {request.path} "
                f"performed {total_query_count} queries"
            )
        
        # Add header for development debugging
        response['X-Query-Count'] = str(total_query_count)
        
        return response


class APIAccessLoggingMiddleware:
    """
    Middleware to log all API access.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only log API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Get start time
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the API access
        user_id = getattr(request.user, 'id', None)
        username = getattr(request.user, 'username', 'anonymous')
        
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user_id': user_id,
            'username': username,
            'ip': self._get_client_ip(request),
            'status_code': response.status_code,
            'duration': f"{duration:.3f}s",
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
        }
        
        # Log at different levels based on response status
        if response.status_code >= 500:
            logger.error(f"API error: {json.dumps(log_data)}")
        elif response.status_code >= 400:
            logger.warning(f"API client error: {json.dumps(log_data)}")
        else:
            logger.info(f"API access: {json.dumps(log_data)}")
        
        return response
    
    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get leftmost IP in the chain (client's IP)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip