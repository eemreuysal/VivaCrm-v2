"""
Query optimization utilities for VivaCRM v2.

This module provides utilities for optimizing database queries,
fixing N+1 query problems, and tracking query usage.
"""
import functools
import logging
import time
import inspect
from typing import Dict, List, Any, Callable, Optional, Union, Set, Tuple
from django.db import connection, reset_queries
from django.db.models import QuerySet, Model
from django.conf import settings
from django.utils.timezone import now

logger = logging.getLogger(__name__)


def count_queries(reset: bool = True) -> int:
    """
    Count the number of queries executed.
    This only works when DEBUG is True.
    
    Args:
        reset: Whether to reset the query count after counting
        
    Returns:
        int: Number of queries executed
    """
    if not settings.DEBUG:
        return 0
    
    count = len(connection.queries)
    
    if reset:
        reset_queries()
    
    return count


def log_queries(func: Callable) -> Callable:
    """
    Decorator to log queries executed by a function.
    This only works when DEBUG is True.
    
    Args:
        func: Function to decorate
        
    Returns:
        callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        start_time = time.time()
        reset_queries()
        
        result = func(*args, **kwargs)
        
        execution_time = time.time() - start_time
        query_count = len(connection.queries)
        
        module = func.__module__
        function_name = func.__name__
        
        # Log query count and time
        logger.info(
            f"{module}.{function_name} executed {query_count} queries "
            f"in {execution_time:.4f} seconds"
        )
        
        # Log individual queries if too many
        if query_count > 10:
            logger.warning(
                f"{module}.{function_name} executed {query_count} queries - "
                f"possible N+1 query problem"
            )
            
            # Log the actual queries for debugging
            if logger.isEnabledFor(logging.DEBUG):
                for i, query in enumerate(connection.queries):
                    time_ms = float(query.get('time', 0)) * 1000
                    sql = query.get('sql', '')
                    logger.debug(f"Query {i+1} ({time_ms:.2f}ms): {sql}")
        
        return result
    
    return wrapper


def optimize_queryset(queryset: QuerySet, 
                      select_related: Optional[List[str]] = None, 
                      prefetch_related: Optional[List[str]] = None,
                      annotation_callback: Optional[Callable[[QuerySet], QuerySet]] = None) -> QuerySet:
    """
    Optimize a queryset by adding select_related and prefetch_related.
    
    Args:
        queryset: The queryset to optimize
        select_related: List of fields to select_related
        prefetch_related: List of fields to prefetch_related
        annotation_callback: Optional callback to add annotations
        
    Returns:
        QuerySet: The optimized queryset
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    if annotation_callback:
        queryset = annotation_callback(queryset)
    
    return queryset


def detect_n_plus_1(queryset: QuerySet, n: int = 5, 
                    access_related: bool = True,
                    expected_query_count: int = 3) -> Dict[str, Any]:
    """
    Detect N+1 query problems by evaluating a queryset and accessing fields.
    
    Args:
        queryset: The queryset to evaluate
        n: Number of objects to evaluate (default: 5)
        access_related: Whether to access related fields
        expected_query_count: Expected number of queries (default: 3)
        
    Returns:
        dict: Detection results with fields:
          - initial_query_count: Number of queries to evaluate the queryset
          - access_query_count: Number of queries when accessing fields
          - total_query_count: Total number of queries
          - has_n_plus_1: Whether an N+1 problem was detected
          - related_fields: List of related fields that caused queries
    """
    if not settings.DEBUG:
        return {'has_n_plus_1': False, 'error': 'DEBUG is False, cannot detect N+1 problems'}
    
    reset_queries()
    
    # Slice queryset to limit objects
    queryset = queryset[:n]
    
    # Evaluate queryset
    objects = list(queryset)
    initial_query_count = len(connection.queries)
    
    if not objects:
        return {
            'initial_query_count': initial_query_count,
            'access_query_count': 0,
            'total_query_count': initial_query_count,
            'has_n_plus_1': False,
            'related_fields': []
        }
    
    # Reset query count
    reset_queries()
    
    # Get all field names
    model = queryset.model
    field_names = [field.name for field in model._meta.fields]
    related_fields = [field.name for field in model._meta.fields if field.is_relation]
    
    # Access fields to trigger related queries
    triggered_fields = []
    
    for obj in objects:
        # Access all fields
        for field_name in field_names:
            try:
                getattr(obj, field_name)
            except Exception:
                pass
        
        # Access related fields if requested
        if access_related:
            for field_name in related_fields:
                try:
                    related_obj = getattr(obj, field_name)
                    # Access id to force evaluation if it's a descriptor
                    if related_obj is not None:
                        getattr(related_obj, 'id', None)
                    if field_name not in triggered_fields and len(connection.queries) > 0:
                        triggered_fields.append(field_name)
                except Exception:
                    pass
    
    # Count queries
    access_query_count = len(connection.queries)
    total_query_count = initial_query_count + access_query_count
    
    # Determine if N+1 problem exists
    has_n_plus_1 = access_query_count > expected_query_count
    
    return {
        'initial_query_count': initial_query_count,
        'access_query_count': access_query_count,
        'total_query_count': total_query_count,
        'has_n_plus_1': has_n_plus_1,
        'related_fields': triggered_fields
    }


def suggest_queryset_optimization(queryset: QuerySet) -> Dict[str, Any]:
    """
    Analyze a queryset and suggest optimizations.
    
    Args:
        queryset: The queryset to analyze
        
    Returns:
        dict: Optimization suggestions with fields:
          - select_related: List of fields to select_related
          - prefetch_related: List of fields to prefetch_related
          - filtering: List of filtering suggestions
          - indices: List of suggested indices
    """
    # Detect N+1 problems
    detection = detect_n_plus_1(queryset)
    
    model = queryset.model
    model_name = model.__name__
    
    # Analyze queryset and build suggestions
    suggestions = {
        'model': model_name,
        'select_related': [],
        'prefetch_related': [],
        'filtering': [],
        'indices': [],
        'has_n_plus_1': detection['has_n_plus_1'],
        'query_count': detection['total_query_count']
    }
    
    # Add related fields based on detection
    for field_name in detection['related_fields']:
        field = model._meta.get_field(field_name)
        
        if field.many_to_one or field.one_to_one:
            # ForeignKey or OneToOneField -> select_related
            suggestions['select_related'].append(field_name)
        elif field.one_to_many or field.many_to_many:
            # ManyToManyField or reverse ForeignKey -> prefetch_related
            suggestions['prefetch_related'].append(field_name)
    
    # Suggest indexes
    for field in model._meta.fields:
        if field.db_index:
            continue
        
        # Suggest indexes for ForeignKey fields
        if field.is_relation and field.many_to_one:
            suggestions['indices'].append(f"{field.name}_id")
        
        # Suggest indexes for fields likely used in filtering
        if field.name in ['status', 'is_active', 'type', 'created_at', 'updated_at']:
            suggestions['indices'].append(field.name)
        
        # Suggest indexes for fields likely used in searching
        if 'name' in field.name or 'email' in field.name or 'code' in field.name:
            suggestions['indices'].append(field.name)
    
    # Suggest optimized filtering if filters are present
    if hasattr(queryset, 'query') and queryset.query.where:
        suggestions['filtering'].append("Use filter(field=value) instead of filter(field__exact=value)")
        suggestions['filtering'].append("Add appropriate indices for filtered fields")
        suggestions['filtering'].append("Consider using Q objects with operator & instead of multiple filters")
    
    return suggestions


def apply_suggested_optimizations(queryset: QuerySet) -> QuerySet:
    """
    Apply suggested optimizations to a queryset.
    
    Args:
        queryset: The queryset to optimize
        
    Returns:
        QuerySet: The optimized queryset
    """
    suggestions = suggest_queryset_optimization(queryset)
    
    # Apply select_related and prefetch_related
    if suggestions['select_related']:
        queryset = queryset.select_related(*suggestions['select_related'])
    
    if suggestions['prefetch_related']:
        queryset = queryset.prefetch_related(*suggestions['prefetch_related'])
    
    return queryset


class QueryCountMiddleware:
    """
    Middleware to count queries per request and log slow queries.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Reset query count
        reset_queries()
        
        # Process request
        start_time = time.time()
        response = self.get_response(request)
        execution_time = time.time() - start_time
        
        # Count queries
        query_count = len(connection.queries)
        
        # Add headers
        response['X-Query-Count'] = str(query_count)
        response['X-Execution-Time'] = f"{execution_time:.4f}s"
        
        # Log if too many queries
        if query_count > 50:
            logger.warning(
                f"Request to {request.path} executed {query_count} queries "
                f"in {execution_time:.4f} seconds - possible N+1 query problem"
            )
            
            # Log detailed query info
            queries_by_type = {}
            for query in connection.queries:
                sql = query.get('sql', '')
                
                # Extract query type
                query_type = 'other'
                if sql.startswith('SELECT'):
                    query_type = 'select'
                elif sql.startswith('INSERT'):
                    query_type = 'insert'
                elif sql.startswith('UPDATE'):
                    query_type = 'update'
                elif sql.startswith('DELETE'):
                    query_type = 'delete'
                
                # Group by type
                if query_type not in queries_by_type:
                    queries_by_type[query_type] = 0
                queries_by_type[query_type] += 1
            
            # Log query types
            for query_type, count in queries_by_type.items():
                logger.warning(f"  - {count} {query_type.upper()} queries")
        
        return response


# Dictionary mapping model names to optimized querysets
OPTIMIZED_QUERYSETS = {
    'Customer': {
        'select_related': ['owner'],
        'prefetch_related': ['addresses', 'contacts', 'orders'],
    },
    'Order': {
        'select_related': ['customer', 'owner'],
        'prefetch_related': ['items', 'items__product', 'payments', 'shipments'],
    },
    'Product': {
        'select_related': ['category'],
        'prefetch_related': [],
    },
    'Invoice': {
        'select_related': ['customer', 'order'],
        'prefetch_related': ['items', 'items__product'],
    },
}


def get_optimized_queryset(model_name: str, queryset: QuerySet) -> QuerySet:
    """
    Get an optimized queryset for a model.
    
    Args:
        model_name: Name of the model
        queryset: The original queryset
        
    Returns:
        QuerySet: The optimized queryset
    """
    if model_name in OPTIMIZED_QUERYSETS:
        optimizations = OPTIMIZED_QUERYSETS[model_name]
        
        if 'select_related' in optimizations and optimizations['select_related']:
            queryset = queryset.select_related(*optimizations['select_related'])
        
        if 'prefetch_related' in optimizations and optimizations['prefetch_related']:
            queryset = queryset.prefetch_related(*optimizations['prefetch_related'])
    
    return queryset