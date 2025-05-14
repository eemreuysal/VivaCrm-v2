"""
Cache middleware for VivaCRM v2.

This module provides middleware for enhancing caching behavior.
"""
import time
import logging
import re
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse
from django.core.cache import cache
from core.cache import generate_cache_key

logger = logging.getLogger(__name__)


class CacheMonitoringMiddleware:
    """
    Middleware to monitor cache usage.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total': 0
        }
    
    def __call__(self, request):
        # Store original cache functions
        original_get = cache.get
        original_set = cache.set
        
        # Replace with monitored versions
        def monitored_get(key, default=None, **kwargs):
            self.cache_stats['total'] += 1
            result = original_get(key, default, **kwargs)
            if result is None:
                self.cache_stats['misses'] += 1
            else:
                self.cache_stats['hits'] += 1
            return result
        
        cache.get = monitored_get
        
        # Process request
        start_time = time.time()
        response = self.get_response(request)
        request_time = time.time() - start_time
        
        # Restore original functions
        cache.get = original_get
        cache.set = original_set
        
        # Add cache stats to response headers (in development)
        if request.META.get('HTTP_X_CACHE_STATS') == 'true':
            response['X-Cache-Hits'] = str(self.cache_stats['hits'])
            response['X-Cache-Misses'] = str(self.cache_stats['misses'])
            response['X-Cache-Total'] = str(self.cache_stats['total'])
            response['X-Cache-Hit-Ratio'] = '{:.2f}%'.format(
                (self.cache_stats['hits'] / self.cache_stats['total'] * 100) 
                if self.cache_stats['total'] > 0 else 0
            )
            response['X-Request-Time'] = '{:.4f}s'.format(request_time)
        
        return response


class CachePurgeSignalMiddleware:
    """
    Middleware to process cache purge signals from HTTP requests.
    
    This allows admin actions to purge cache via special headers.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request first
        response = self.get_response(request)
        
        # Check if request contains a cache purge header
        purge_key = request.META.get('HTTP_X_CACHE_PURGE_KEY')
        purge_prefix = request.META.get('HTTP_X_CACHE_PURGE_PREFIX')
        
        if purge_key or purge_prefix:
            # Check authentication - only allow staff to purge cache
            if hasattr(request, 'user') and request.user.is_staff:
                from core.cache import invalidate_cache_key, invalidate_cache_prefix
                
                if purge_key:
                    invalidate_cache_key(purge_key)
                    logger.info(f"Cache key purged by {request.user.username}: {purge_key}")
                    response['X-Cache-Purged-Key'] = purge_key
                
                if purge_prefix:
                    invalidate_cache_prefix(purge_prefix)
                    logger.info(f"Cache prefix purged by {request.user.username}: {purge_prefix}")
                    response['X-Cache-Purged-Prefix'] = purge_prefix
            else:
                logger.warning(f"Unauthorized cache purge attempt from IP {request.META.get('REMOTE_ADDR')}")
        
        return response


class ConditionalCacheMiddleware:
    """
    Middleware to conditionally cache responses based on the request
    and response attributes.
    """
    # List of URL patterns to exclude from caching
    EXCLUDE_URLS = [
        r'^/admin/',
        r'^/accounts/login',
        r'^/accounts/logout',
    ]
    
    # Maximum content length to cache (to avoid filling cache with large responses)
    MAX_CONTENT_LENGTH = 1_000_000  # 1MB
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this request should be excluded from caching
        if self._should_exclude_request(request):
            return self.get_response(request)
        
        # Try to get cached response
        cache_key = self._get_cache_key(request)
        cached_response = cache.get(cache_key)
        
        if cached_response:
            # Add cache hit header and return cached response
            logger.debug(f"Cache hit for {request.path}")
            cached_response['X-Cache'] = 'HIT'
            return cached_response
        
        # Cache miss, process request normally
        logger.debug(f"Cache miss for {request.path}")
        response = self.get_response(request)
        
        # Check if response should be cached
        if self._should_cache_response(request, response):
            # Set a short default cache timeout to avoid stale data
            timeout = 300  # 5 minutes
            
            # Store response in cache
            cache.set(cache_key, response, timeout)
            logger.debug(f"Cached response for {request.path} for {timeout}s")
            
            # Add cache miss header
            response['X-Cache'] = 'MISS'
        
        return response
    
    def _should_exclude_request(self, request):
        """
        Check if a request should be excluded from caching.
        """
        # Only cache GET requests
        if request.method != 'GET':
            return True
        
        # Exclude authenticated requests (except API requests with authentication tokens)
        if hasattr(request, 'user') and request.user.is_authenticated and 'api' not in request.path:
            return True
        
        # Exclude URLs matching patterns
        for pattern in self.EXCLUDE_URLS:
            if re.match(pattern, request.path):
                return True
        
        return False
    
    def _should_cache_response(self, request, response):
        """
        Check if a response should be cached.
        """
        # Only cache 200 OK responses
        if response.status_code != 200:
            return False
        
        # Don't cache responses with "Cache-Control: no-cache" or similar
        no_cache_directives = ['no-cache', 'no-store', 'private']
        cache_control = response.get('Cache-Control', '')
        if any(directive in cache_control for directive in no_cache_directives):
            return False
        
        # Don't cache large responses
        if len(response.content) > self.MAX_CONTENT_LENGTH:
            return False
        
        # Don't cache responses with Set-Cookie headers
        if response.has_header('Set-Cookie'):
            return False
        
        return True
    
    def _get_cache_key(self, request):
        """
        Generate a cache key for the request.
        """
        # Create a comprehensive key based on the path and query
        query_string = request.META.get('QUERY_STRING', '')
        key_parts = [
            'response_cache',
            request.path,
            query_string
        ]
        
        # Add any cache-relevant headers
        cache_control = request.META.get('HTTP_CACHE_CONTROL', '')
        if cache_control:
            key_parts.append(cache_control)
        
        accept = request.META.get('HTTP_ACCEPT', '')
        if accept:
            key_parts.append(accept)
        
        return generate_cache_key(*key_parts)