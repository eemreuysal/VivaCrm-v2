"""
Celery tasks for the Dashboard app.

This module defines Celery tasks for managing dashboard data caching.
These tasks handle refreshing, cleaning, and updating dashboard caches
to ensure optimal performance and data freshness.
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from django.db.models import F

from .cache_helpers import (
    refresh_dashboard_caches,
    invalidate_dashboard_caches,
    get_cached_dashboard_stats,
    get_cached_chart_data,
    get_cached_low_stock_products
)

logger = logging.getLogger(__name__)


@shared_task
def refresh_dashboard_data():
    """
    Refresh all dashboard data caches.
    
    This task is designed to run periodically (e.g., every hour) to ensure
    that dashboard data is always fresh when users access the dashboard.
    This prevents the first user from experiencing a slow load time.
    """
    try:
        logger.info("Starting dashboard data refresh task")
        
        # Refresh for different time periods
        for period in ['day', 'week', 'month']:
            refresh_dashboard_caches(period=period)
        
        # Low stock is independent of time period
        get_cached_low_stock_products(limit=20, threshold_ratio=1.0)
        
        logger.info("Dashboard data refresh completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {str(e)}", exc_info=True)
        return False


@shared_task
def clean_old_dashboard_caches():
    """
    Clean up old dashboard caches that might have accumulated.
    
    This task is designed to run less frequently (e.g., once a day)
    to clean up any cache keys that might have accumulated due to
    custom date ranges.
    """
    try:
        logger.info("Starting dashboard cache cleanup task")
        
        # Invalidate all dashboard caches
        invalidate_dashboard_caches()
        
        # Then refresh the common ones that are actually used
        refresh_dashboard_data.delay()
        
        logger.info("Dashboard cache cleanup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error cleaning dashboard caches: {str(e)}", exc_info=True)
        return False


@shared_task
def update_dashboard_on_data_change(model_name, object_id=None):
    """
    Update dashboard data when relevant models change.
    
    This task is triggered by signals from models that affect dashboard data,
    such as Order, Customer, Product, etc.
    
    Args:
        model_name: The name of the model that changed
        object_id: Optional ID of the specific object that changed
    """
    try:
        logger.info(f"Updating dashboard data after {model_name} change")
        
        # Determine which caches to invalidate based on the model
        if model_name in ['Order', 'OrderItem']:
            # Orders affect sales charts and dashboard stats
            invalidate_dashboard_caches()
        elif model_name in ['ProductStock', 'StockMovement']:
            # Stock değişiklikleri için sadece ilgili cache'leri güncelle
            get_cached_low_stock_products(limit=20, refresh=True)
            get_cached_chart_data('products', 'month', refresh=True)
        elif model_name == 'Product':
            # Products affect product charts and low stock
            get_cached_low_stock_products(limit=20, refresh=True)
            get_cached_chart_data('products', 'month', refresh=True)
        elif model_name == 'Customer':
            # Customers affect dashboard stats
            get_cached_dashboard_stats(refresh=True)
            get_cached_chart_data('customers', 'month', refresh=True)
        elif model_name == 'OrderStatus':
            # Sipariş durumu değişiklikleri
            get_cached_dashboard_stats(refresh=True)
            get_cached_chart_data('orders', 'month', refresh=True)
        elif model_name == 'CompletedOrder':
            # Tamamlanmış siparişler satış istatistiklerini etkiler
            get_cached_dashboard_stats(refresh=True)
            get_cached_chart_data('sales', 'month', refresh=True)
            get_cached_chart_data('orders', 'month', refresh=True)
        elif model_name == 'CancelledOrder':
            # İptal edilen siparişler
            get_cached_dashboard_stats(refresh=True)
            get_cached_chart_data('orders', 'month', refresh=True)
        else:
            # For any other model, just refresh everything
            invalidate_dashboard_caches()
        
        return True
    except Exception as e:
        logger.error(f"Error updating dashboard data: {str(e)}", exc_info=True)
        return False


@shared_task
def generate_dashboard_cache_data():
    """
    Generate all dashboard cache data for common views.
    
    This task is designed to run daily during low-traffic hours to
    pre-populate caches for all common dashboard views. This ensures
    that dashboard data is always fresh and quickly accessible.
    
    It performs a more comprehensive refresh than the hourly
    refresh_dashboard_data task, including custom time periods
    and all chart types.
    """
    try:
        logger.info("Starting comprehensive dashboard cache generation")
        
        # First clean up any old caches
        invalidate_dashboard_caches()
        
        # Refresh stats for standard time periods
        time_periods = ['day', 'week', 'month', 'year']
        for period in time_periods:
            get_cached_dashboard_stats(refresh=True, period=period)
            
        # Refresh all chart types for all time periods
        chart_types = ['sales', 'products', 'orders', 'customers']
        for chart_type in chart_types:
            for period in time_periods:
                get_cached_chart_data(chart_type, period, refresh=True)
        
        # Refresh low stock products with different limits
        for limit in [10, 20, 50]:
            get_cached_low_stock_products(limit=limit, refresh=True)
        
        # Generate quarter and year-to-date stats
        now = timezone.now()
        # YTD - Year to date
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        get_cached_dashboard_stats(
            refresh=True, 
            start_date=start_of_year.strftime('%Y-%m-%d'), 
            end_date=now.strftime('%Y-%m-%d')
        )
        
        # QTD - Quarter to date
        current_quarter = ((now.month - 1) // 3) + 1
        start_of_quarter = now.replace(
            month=((current_quarter - 1) * 3) + 1,
            day=1, 
            hour=0, 
            minute=0, 
            second=0, 
            microsecond=0
        )
        get_cached_dashboard_stats(
            refresh=True, 
            start_date=start_of_quarter.strftime('%Y-%m-%d'), 
            end_date=now.strftime('%Y-%m-%d')
        )
        
        logger.info("Comprehensive dashboard cache generation completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error generating dashboard cache data: {str(e)}", exc_info=True)
        return False


@shared_task
def monitor_dashboard_performance():
    """
    Monitor dashboard performance metrics and log any issues.
    
    This task collects performance metrics for dashboard views and API endpoints,
    logs any performance issues, and can trigger alerts for slow endpoints.
    """
    from django.db import connection
    from core.performance_monitoring import get_endpoint_metrics, log_performance_alert
    
    try:
        logger.info("Starting dashboard performance monitoring task")
        
        # Get performance metrics for dashboard endpoints
        dashboard_endpoints = [
            '/dashboard/',
            '/dashboard/content/',
            '/dashboard/api/chart-data/',
            '/dashboard/api/stats/',
            '/dashboard/api/low-stock/'
        ]
        
        for endpoint in dashboard_endpoints:
            metrics = get_endpoint_metrics(endpoint)
            if metrics:
                avg_response_time = metrics.get('avg_response_time', 0)
                p95_response_time = metrics.get('p95_response_time', 0)
                error_rate = metrics.get('error_rate', 0)
                
                # Log performance issues
                if avg_response_time > 500:  # More than 500ms
                    log_performance_alert(
                        endpoint=endpoint,
                        metric='avg_response_time',
                        value=avg_response_time,
                        threshold=500
                    )
                
                if p95_response_time > 1000:  # More than 1 second
                    log_performance_alert(
                        endpoint=endpoint,
                        metric='p95_response_time',
                        value=p95_response_time,
                        threshold=1000
                    )
                
                if error_rate > 0.05:  # More than 5% error rate
                    log_performance_alert(
                        endpoint=endpoint,
                        metric='error_rate',
                        value=error_rate,
                        threshold=0.05
                    )
        
        # Check query counts
        with connection.execute_wrapper(lambda execute, sql, params, many, context: logger.debug(f"SQL: {sql}")):
            # This will log all SQL queries executed when getting dashboard stats
            get_cached_dashboard_stats(refresh=True)
        
        logger.info("Dashboard performance monitoring completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error monitoring dashboard performance: {str(e)}", exc_info=True)
        return False