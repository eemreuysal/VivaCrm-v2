"""
Cache helper functions for the Dashboard app.
"""
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from typing import Dict, Any, Optional, List, Union
from core.cache import cache_method, generate_cache_key

logger = logging.getLogger(__name__)

# Cache timeouts (in seconds)
DASHBOARD_STATS_TIMEOUT = 60 * 15  # 15 minutes
CHART_DATA_TIMEOUT = 60 * 60 * 2   # 2 hours
LOW_STOCK_TIMEOUT = 60 * 30        # 30 minutes


def get_cached_dashboard_stats(refresh: bool = False) -> Dict[str, Any]:
    """
    Get dashboard statistics from cache or compute and cache them.
    
    Args:
        refresh: Force refresh the cache
        
    Returns:
        dict: Dashboard statistics
    """
    cache_key = "dashboard:stats"
    
    # Return from cache if available and not forcing refresh
    if not refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Using cached dashboard stats")
            return cached_data
    
    # Import here to avoid circular imports
    from .views import get_dashboard_data
    
    # Get fresh dashboard data
    logger.debug(f"Computing fresh dashboard stats")
    stats = get_dashboard_data()
    
    # Cache the result
    cache.set(cache_key, stats, DASHBOARD_STATS_TIMEOUT)
    
    return stats


def get_cached_chart_data(chart_type: str, period: str = 'month') -> Dict[str, Any]:
    """
    Get chart data from cache or compute and cache it.
    
    Args:
        chart_type: Type of chart (sales, products, etc.)
        period: Time period (day, week, month, year)
        
    Returns:
        dict: Chart data
    """
    cache_key = f"dashboard:chart:{chart_type}:{period}"
    
    # Return from cache if available
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Using cached chart data for {chart_type} ({period})")
        return cached_data
    
    # Import here to avoid circular imports
    from .views import get_chart_data
    
    # Get fresh chart data
    logger.debug(f"Computing fresh chart data for {chart_type} ({period})")
    data = get_chart_data(chart_type, period)
    
    # Cache the result
    cache.set(cache_key, data, CHART_DATA_TIMEOUT)
    
    return data


def get_cached_low_stock_products(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get low stock products from cache or compute and cache them.
    
    Args:
        limit: Maximum number of products to return
        
    Returns:
        list: List of low stock products
    """
    cache_key = f"dashboard:low_stock_products:{limit}"
    
    # Return from cache if available
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Using cached low stock products")
        return cached_data
    
    # Import here to avoid circular imports
    from products.models import Product
    from django.db.models import F
    
    # Get low stock products
    logger.debug(f"Computing fresh low stock products")
    products = list(
        Product.objects.filter(
            stock__lt=F('threshold_stock'),
            threshold_stock__gt=0
        ).order_by(
            F('stock') / F('threshold_stock')
        )[:limit].values(
            'id', 'name', 'sku', 'stock', 'threshold_stock',
            'category__name'
        )
    )
    
    # Calculate percentage for each product
    for product in products:
        if product['threshold_stock'] > 0:
            product['stock_percentage'] = round(
                (product['stock'] / product['threshold_stock']) * 100, 2
            )
        else:
            product['stock_percentage'] = 100
    
    # Cache the result
    cache.set(cache_key, products, LOW_STOCK_TIMEOUT)
    
    return products


def invalidate_dashboard_caches():
    """
    Invalidate all dashboard-related caches.
    """
    # Get all cache keys with dashboard prefix
    from core.cache import invalidate_cache_prefix
    
    logger.info(f"Invalidating all dashboard caches")
    invalidate_cache_prefix("dashboard:")


def invalidate_chart_cache(chart_type: Optional[str] = None):
    """
    Invalidate chart data caches.
    
    Args:
        chart_type: Optional specific chart type to invalidate
    """
    from core.cache import invalidate_cache_prefix
    
    if chart_type:
        logger.info(f"Invalidating cache for chart: {chart_type}")
        invalidate_cache_prefix(f"dashboard:chart:{chart_type}")
    else:
        logger.info(f"Invalidating all chart caches")
        invalidate_cache_prefix("dashboard:chart:")