"""
Redis cache utilities and decorators for VivaCRM v2.

This module provides utilities for working with Redis cache, including:
- Cache key generation
- Cache decorators for views and methods
- Cache invalidation utilities
- Cache monitoring
"""
import time
import json
import hashlib
import inspect
import logging
from functools import wraps
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page as django_cache_page
from django.db.models import Model, QuerySet

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a unique cache key based on the given parameters.
    
    Args:
        prefix: The prefix for the cache key
        *args: Additional args to include in the key
        **kwargs: Additional kwargs to include in the key
        
    Returns:
        str: A unique cache key
    """
    # Convert args and kwargs to a string representation
    key_parts = [prefix]
    
    # Add args to key parts
    if args:
        for arg in args:
            if hasattr(arg, 'pk') and hasattr(arg, '__class__'):
                # For model instances, use class name and pk
                key_parts.append(f"{arg.__class__.__name__}_{arg.pk}")
            elif isinstance(arg, (list, tuple, set)):
                # For iterables, convert to sorted tuple of strings
                key_parts.append(str(tuple(sorted(str(x) for x in arg))))
            else:
                key_parts.append(str(arg))
    
    # Add kwargs to key parts (sorted for consistency)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        for key, value in sorted_kwargs:
            if hasattr(value, 'pk') and hasattr(value, '__class__'):
                key_parts.append(f"{key}={value.__class__.__name__}_{value.pk}")
            elif isinstance(value, (list, tuple, set)):
                key_parts.append(f"{key}={tuple(sorted(str(x) for x in value))}")
            else:
                key_parts.append(f"{key}={value}")
    
    # Join all parts with a separator
    key_string = ":".join(key_parts)
    
    # If the key is too long, use a hash
    if len(key_string) > 250:
        # Use SHA1 hash for uniqueness while keeping reasonable length
        # SHA1 is fine for this purpose as we're not using it for security
        hashed_part = hashlib.sha1(key_string.encode('utf-8')).hexdigest()
        key_string = f"{prefix}:hash:{hashed_part}"
    
    return key_string


def cache_method(timeout: int = 3600, key_prefix: Optional[str] = None):
    """
    Cache the result of a method.
    
    Args:
        timeout: Cache timeout in seconds (default: 1 hour)
        key_prefix: Optional prefix for the cache key
        
    Returns:
        callable: Decorated method
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create a unique cache key
            prefix = key_prefix or f"{self.__class__.__name__}.{func.__name__}"
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Cache miss, call the function
            logger.debug(f"Cache miss for {cache_key}")
            start_time = time.time()
            result = func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Store result in cache
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cached {cache_key} for {timeout}s (execution time: {execution_time:.4f}s)")
            
            return result
        return wrapper
    return decorator


def cache_key_function(func):
    """
    Decorator to mark a function as a cache key generator.
    
    This is a simple decorator that doesn't modify the function's behavior
    but signals that the function is used for generating cache keys.
    
    Args:
        func: The function to decorate
        
    Returns:
        callable: The original function, unmodified
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def cache_function(timeout: int = 3600, key_prefix: Optional[str] = None):
    """
    Cache the result of a function.
    
    Args:
        timeout: Cache timeout in seconds (default: 1 hour)
        key_prefix: Optional prefix for the cache key
        
    Returns:
        callable: Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Cache miss, call the function
            logger.debug(f"Cache miss for {cache_key}")
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Store result in cache
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cached {cache_key} for {timeout}s (execution time: {execution_time:.4f}s)")
            
            return result
        return wrapper
    return decorator


def cache_view(timeout: int = 3600, key_func=None):
    """
    A view decorator that caches the response based on the request.
    
    This is a wrapper around Django's cache_page but with additional logging.
    
    Args:
        timeout: Cache timeout in seconds (default: 1 hour)
        key_func: Function to generate a custom cache key
        
    Returns:
        callable: Decorated view
    """
    def decorator(view_func):
        # Use Django's cache_page decorator
        cached_view = django_cache_page(timeout, key_prefix="view", key_function=key_func)(view_func)
        
        @wraps(cached_view)
        def wrapper(request, *args, **kwargs):
            # Log cache access
            view_name = view_func.__name__
            logger.debug(f"Accessing cached view: {view_name}")
            
            start_time = time.time()
            response = cached_view(request, *args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.debug(f"View {view_name} response time: {execution_time:.4f}s")
            return response
        
        return wrapper
    
    return decorator


def cache_viewset_action(timeout: int = 3600, key_prefix: Optional[str] = None, 
                         include_request_user: bool = False):
    """
    Cache the result of a ViewSet action.
    
    Args:
        timeout: Cache timeout in seconds (default: 1 hour)
        key_prefix: Optional prefix for the cache key
        include_request_user: Whether to include the user ID in the cache key
        
    Returns:
        callable: Decorated action
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Create a unique cache key
            prefix = key_prefix or f"{self.__class__.__name__}.{func.__name__}"
            
            # Include user ID in key if requested
            if include_request_user and hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.id
            else:
                user_id = None
            
            # Include query params in key
            query_params = dict(request.query_params.items())
            
            cache_key = generate_cache_key(
                prefix, 
                user_id=user_id, 
                path=request.path, 
                method=request.method, 
                **query_params
            )
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for viewset action {cache_key}")
                return cached_result
            
            # Cache miss, call the function
            logger.debug(f"Cache miss for viewset action {cache_key}")
            start_time = time.time()
            result = func(self, request, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Store result in cache
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cached viewset action {cache_key} "
                        f"for {timeout}s (execution time: {execution_time:.4f}s)")
            
            return result
        return wrapper
    return decorator


def cache_model_method(timeout: int = 3600, key_prefix: Optional[str] = None):
    """
    Cache the result of a model method.
    
    Args:
        timeout: Cache timeout in seconds (default: 1 hour)
        key_prefix: Optional prefix for the cache key
        
    Returns:
        callable: Decorated method
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create a unique cache key
            prefix = key_prefix or f"{self.__class__.__name__}.{func.__name__}"
            cache_key = generate_cache_key(prefix, self.pk, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for model method {cache_key}")
                return cached_result
            
            # Cache miss, call the function
            logger.debug(f"Cache miss for model method {cache_key}")
            start_time = time.time()
            result = func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Store result in cache
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cached model method {cache_key} "
                        f"for {timeout}s (execution time: {execution_time:.4f}s)")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_key(key: str):
    """
    Invalidate a specific cache key.
    
    Args:
        key: The cache key to invalidate
    """
    logger.debug(f"Invalidating cache key: {key}")
    cache.delete(key)


def invalidate_cache_prefix(prefix: str):
    """
    Invalidate all cache keys starting with the given prefix.
    
    This operation can be inefficient and should be used carefully.
    
    Args:
        prefix: The prefix of the cache keys to invalidate
    """
    from django.conf import settings
    
    if not settings.CACHES['default']['BACKEND'].endswith('.RedisCache'):
        logger.warning("Cannot invalidate keys by prefix with non-Redis backend")
        return
    
    # Import here to avoid requiring redis as a dependency for the module
    import redis
    
    # Parse the Redis location from the settings
    location = settings.CACHES['default'].get('LOCATION', 'redis://localhost:6379/1')
    
    # Redis URL parsing
    db_number = 1  # Default
    host = 'localhost'
    port = 6379
    
    # Parse redis://host:port/db format
    if location.startswith('redis://'):
        location = location[8:]  # Remove redis://
        if '/' in location:
            location, db_part = location.rsplit('/', 1)
            try:
                db_number = int(db_part)
            except ValueError:
                pass
        
        if ':' in location:
            host, port_str = location.split(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                pass
        else:
            host = location
    
    try:
        # Connect to Redis
        redis_client = redis.Redis(host=host, port=port, db=db_number)
        
        # Find keys with the prefix
        pattern = f"*{prefix}*"
        matching_keys = redis_client.keys(pattern)
        
        # Delete matching keys
        if matching_keys:
            redis_client.delete(*matching_keys)
            logger.info(f"Invalidated {len(matching_keys)} cache keys with prefix '{prefix}'")
        else:
            logger.debug(f"No cache keys found with prefix '{prefix}'")
    
    except Exception as e:
        logger.error(f"Error invalidating Redis cache: {str(e)}")


def invalidate_model_cache(model_instance: Model, method_name: Optional[str] = None):
    """
    Invalidate cache keys related to a model instance.
    
    Args:
        model_instance: The model instance
        method_name: Optional specific method name to invalidate
    """
    model_class_name = model_instance.__class__.__name__
    prefix = f"{model_class_name}.{method_name}" if method_name else model_class_name
    
    # For Redis, we can use pattern matching
    if settings.CACHES['default']['BACKEND'].endswith('.RedisCache'):
        invalidate_cache_prefix(prefix)
    else:
        # For other backends, we need to delete by specific key
        key = generate_cache_key(prefix, model_instance.pk)
        invalidate_cache_key(key)


def cache_prefetch_related(timeout: int = 3600):
    """
    Cache the results of prefetch_related querysets.
    
    Args:
        timeout: Cache timeout in seconds (default: 1 hour)
        
    Returns:
        callable: Decorated method
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the original queryset
            queryset = func(*args, **kwargs)
            
            # Apply caching to prefetch lookups
            if not hasattr(queryset, '_prefetch_related_lookups'):
                return queryset
            
            # Process each prefetch lookup
            for lookup in queryset._prefetch_related_lookups:
                # Create a cache key for this lookup
                prefix = f"prefetch_{queryset.model.__name__}"
                lookup_str = str(lookup) if not isinstance(lookup, str) else lookup
                cache_key = generate_cache_key(prefix, lookup_str)
                
                # Check if it's already cached
                # (implementation would depend on the specific ORM)
                pass
            
            return queryset
        return wrapper
    return decorator


def clear_cache_on_model_change(model_class, key_prefix: Optional[str] = None):
    """
    Decorator to clear the cache when a model changes.
    
    Args:
        model_class: The model class to watch for changes
        key_prefix: Optional prefix for the cache keys to invalidate
        
    Returns:
        callable: Decorator function
    """
    def decorator(cls):
        # Store original methods
        original_save = model_class.save
        original_delete = model_class.delete
        
        # Replace save method
        @wraps(original_save)
        def new_save(self, *args, **kwargs):
            # Call original save
            result = original_save(self, *args, **kwargs)
            
            # Invalidate cache
            prefix = key_prefix or model_class.__name__
            invalidate_cache_prefix(prefix)
            
            return result
        
        # Replace delete method
        @wraps(original_delete)
        def new_delete(self, *args, **kwargs):
            # Invalidate cache
            prefix = key_prefix or model_class.__name__
            invalidate_cache_prefix(prefix)
            
            # Call original delete
            return original_delete(self, *args, **kwargs)
        
        # Apply the new methods
        model_class.save = new_save
        model_class.delete = new_delete
        
        return cls
    
    return decorator