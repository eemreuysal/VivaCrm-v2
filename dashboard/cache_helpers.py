"""
Cache helpers for dashboard data.

This module provides utility functions for caching dashboard data.
It uses Redis cache for storing and retrieving dashboard statistics,
chart data, and other frequently accessed information.
"""

import json
import logging
from functools import wraps
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from django.db.models import F

from core.cache import cache_function, cache_key_function
from products.models import Product
from .services import get_dashboard_data, get_chart_data

logger = logging.getLogger(__name__)


@cache_key_function
def dashboard_stats_cache_key(start_date=None, end_date=None, **kwargs):
    """
    Generate a unique cache key for dashboard statistics.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        str: Cache key for dashboard statistics
    """
    key_parts = ['dashboard:stats']
    
    if start_date:
        key_parts.append(f'start:{start_date}')
    
    if end_date:
        key_parts.append(f'end:{end_date}')
    
    return ':'.join(key_parts)


@cache_key_function
def chart_data_cache_key(chart_type, period='month', **kwargs):
    """
    Generate a unique cache key for chart data.
    
    Args:
        chart_type: Type of chart (sales, products, orders)
        period: Time period (day, week, month, year, custom)
        
    Returns:
        str: Cache key for chart data
    """
    return f'dashboard:chart:{chart_type}:{period}'


@cache_key_function
def low_stock_cache_key(limit=None, **kwargs):
    """
    Generate a unique cache key for low stock products.
    
    Args:
        limit: Maximum number of products to retrieve
        
    Returns:
        str: Cache key for low stock products
    """
    return f'dashboard:low_stock:{limit or "all"}'


def get_cached_dashboard_stats(refresh=False, start_date=None, end_date=None):
    """
    Get dashboard statistics from cache or compute and cache them.
    
    Args:
        refresh: Whether to force a cache refresh
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
        
    Returns:
        dict: Dashboard statistics
    """
    # Generate cache key
    cache_key = dashboard_stats_cache_key(start_date=start_date, end_date=end_date)
    
    # Try to get data from cache first
    if not refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Dashboard stats cache hit for key: {cache_key}")
            return cached_data
    
    # If cache miss or refresh requested, compute data
    logger.debug(f"Dashboard stats cache miss for key: {cache_key}, computing...")
    data = get_dashboard_data(start_date=start_date, end_date=end_date)
    
    # Cache data for 15 minutes
    cache.set(cache_key, data, 15 * 60)
    
    return data


def get_cached_chart_data(chart_type, period='month', refresh=False):
    """
    Get chart data from cache or compute and cache it.
    
    Args:
        chart_type: Type of chart (sales, products, orders)
        period: Time period (day, week, month, year, custom)
        refresh: Whether to force a cache refresh
        
    Returns:
        dict: Chart data
    """
    # Generate cache key
    cache_key = chart_data_cache_key(chart_type=chart_type, period=period)
    
    # Try to get data from cache first
    if not refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Chart data cache hit for key: {cache_key}")
            return cached_data
    
    # If cache miss or refresh requested, compute data
    logger.debug(f"Chart data cache miss for key: {cache_key}, computing...")
    data = get_chart_data(chart_type, period)
    
    # Cache data for 2 hours
    cache.set(cache_key, data, 2 * 60 * 60)
    
    return data


def get_cached_low_stock_products(limit=10, refresh=False, threshold_ratio=1.0):
    """
    Get low stock products from cache or compute and cache them.
    
    Args:
        limit: Maximum number of products to retrieve
        refresh: Whether to force a cache refresh
        threshold_ratio: Ratio to multiply the threshold by (default 1.0)
        
    Returns:
        QuerySet: Low stock products
    """
    # Generate cache key
    cache_key = low_stock_cache_key(limit=limit)
    
    # Try to get data from cache first
    if not refresh:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Low stock products cache hit for key: {cache_key}")
            try:
                # Instead of caching QuerySet directly, we cache the primary keys
                # and then fetch the objects from the database to avoid potential
                # deserialization issues
                product_ids = cached_data
                if product_ids:
                    return Product.objects.filter(
                        id__in=product_ids
                    ).order_by('stock')
                else:
                    return Product.objects.none()
            except Exception as e:
                logger.error(f"Error retrieving low stock products from cache: {e}")
                # Continue to fetch fresh data
    
    # If cache miss or refresh requested, compute data
    logger.debug(f"Low stock products cache miss for key: {cache_key}, computing...")
    
    # Get low stock products based on threshold
    # Düzeltilmiş ORM ifadesi
    products = Product.objects.filter(
        status='available',
        stock__lt=F('threshold_stock') * threshold_ratio
    ).order_by('stock')
    
    if limit:
        products = products[:limit]
    
    # Cache product IDs for 30 minutes
    product_ids = list(products.values_list('id', flat=True))
    cache.set(cache_key, product_ids, 30 * 60)
    
    return products


def invalidate_dashboard_caches():
    """
    Invalidate all dashboard related caches.
    
    This function should be called when data that affects dashboard
    statistics is modified (e.g., new order created, product stock updated).
    """
    logger.debug("Invalidating all dashboard caches...")
    
    # Django cache için daha uyumlu bir yaklaşım kullanın
    from django.conf import settings
    
    # Önbellek Redis ise anahtarları desenle sil
    if settings.CACHES['default']['BACKEND'].endswith('.RedisCache'):
        try:
            # Redis bağlantısı al ve desene göre anahtarları sil
            from core.cache import invalidate_cache_prefix
            invalidate_cache_prefix('dashboard')
            logger.debug("Invalidated dashboard cache keys using Redis pattern matching")
        except Exception as e:
            logger.error(f"Error invalidating Redis cache: {str(e)}")
            # Alternatif yöntem: bilinen önbellek anahtarlarını açıkça sil
            _invalidate_known_dashboard_cache_keys()
    else:
        # Redis olmayan önbellek için bilinen anahtarları açıkça sil
        _invalidate_known_dashboard_cache_keys()


def _invalidate_known_dashboard_cache_keys():
    """
    Bilinen dashboard önbellek anahtarlarını açıkça siler.
    Bu, Redis olmayan cache sistemleri için kullanılır.
    """
    # Genel önbellek anahtarlarını sıfırla
    known_keys = []
    
    # Tüm istatistik anahtarları
    for period in ['day', 'week', 'month', 'year']:
        # Dönemin başlangıç ve bitiş tarihlerini belirle
        start_date = None
        end_date = None
        
        if period == 'day':
            start_date = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif period == 'week':
            start_date = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        elif period == 'month':
            start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif period == 'year':
            start_date = (timezone.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Şu anki tarih
        end_date = timezone.now().strftime('%Y-%m-%d')
        
        # İstatistik anahtarları
        known_keys.append(dashboard_stats_cache_key(start_date=start_date, end_date=end_date))
    
    # Tüm grafik anahtarları
    for chart_type in ['sales', 'products', 'orders']:
        for period in ['day', 'week', 'month', 'year']:
            known_keys.append(chart_data_cache_key(chart_type=chart_type, period=period))
    
    # Düşük stok anahtarları
    for limit in [10, 20, 50, None]:
        known_keys.append(low_stock_cache_key(limit=limit))
    
    # Anahtarları sil
    if known_keys:
        cache.delete_many(known_keys)
        logger.debug(f"Invalidated {len(known_keys)} known dashboard cache keys")


def refresh_dashboard_caches(period=None):
    """
    Refresh all dashboard caches by pre-calculating common data.
    
    This function is designed to be called by a scheduled task to
    pre-populate caches for common dashboard views, improving
    performance for users.
    
    Args:
        period: Optional time period to refresh (day, week, month, year).
               If None, refreshes all periods.
    """
    logger.debug(f"Refreshing dashboard caches for period: {period or 'all'}...")
    
    # Determine periods to refresh
    periods_to_refresh = [period] if period else ['day', 'week', 'month', 'year']
    
    # Refresh main dashboard stats
    for p in periods_to_refresh:
        # Hesaplanan dönem için başlangıç ve bitiş tarihlerini belirle
        start_date, end_date = None, None
        
        if p == 'day':
            # Son 24 saat
            start_date = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = timezone.now().strftime('%Y-%m-%d')
        elif p == 'week':
            # Son 7 gün
            start_date = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = timezone.now().strftime('%Y-%m-%d')
        elif p == 'month':
            # Son 30 gün
            start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = timezone.now().strftime('%Y-%m-%d')
        elif p == 'year':
            # Son 365 gün
            start_date = (timezone.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            end_date = timezone.now().strftime('%Y-%m-%d')
        
        # İstatistikleri yenile
        get_cached_dashboard_stats(refresh=True, start_date=start_date, end_date=end_date)
    
    # Refresh chart data for common periods
    for p in periods_to_refresh:
        for chart_type in ['sales', 'products', 'orders']:
            get_cached_chart_data(chart_type, p, refresh=True)
    
    # Refresh low stock products (period'dan bağımsız)
    get_cached_low_stock_products(refresh=True)
    
    logger.debug("Dashboard cache refresh completed")