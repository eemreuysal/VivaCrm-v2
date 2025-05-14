"""
Dashboard views for VivaCRM v2.

This module provides the views and related utility functions for the dashboard page.
It includes components for displaying key metrics, charts, and summary data.
The dashboard is optimized with caching to reduce database load.
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, F, DecimalField, Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

from customers.models import Customer
from products.models import Product
from orders.models import Order, OrderItem
from core.cache import cache_method, cache_function
from core.query_optimizer import log_queries
from .cache_helpers import (
    get_cached_dashboard_stats, 
    get_cached_chart_data,
    get_cached_low_stock_products
)

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view showing key business metrics and visualizations.
    
    This view assembles the data needed for the dashboard, including:
    - Key performance indicators (KPIs) like total sales, customers, etc.
    - Charts for visualizing sales and product data
    - Low stock alerts
    - Recent orders
    
    Most data is cached to improve performance, with the exception of
    recent orders which are always fetched from the database to ensure freshness.
    """
    template_name = "dashboard/dashboard.html"
    
    @log_queries
    def get_context_data(self, **kwargs):
        """
        Prepare all the data needed for the dashboard.
        
        This method gathers data from various sources, mostly using cached helper
        functions to improve performance. Query counts are logged for optimization.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Context dictionary with all dashboard data
        """
        context = super().get_context_data(**kwargs)
        
        # Force refresh cache if requested
        refresh_cache = self.request.GET.get('refresh_cache') == 'true'
        
        # Get dashboard stats from cache
        dashboard_stats = get_cached_dashboard_stats(refresh=refresh_cache)
        context.update(dashboard_stats)
        
        # Get chart data for different periods
        if 'chart_data' not in context:
            context['chart_data'] = {}
            
        # Add different chart types
        context['chart_data']['sales'] = get_cached_chart_data('sales', 'month')
        context['chart_data']['products'] = get_cached_chart_data('products', 'month')
        
        # Get low stock products
        context['low_stock_products'] = get_cached_low_stock_products(limit=5)
        
        # Recent orders - don't cache these as they change frequently
        # Optimize with select_related to avoid N+1 queries
        context['recent_orders'] = Order.objects.all().select_related(
            'customer', 'owner'
        ).prefetch_related(
            'items', 'items__product'
        ).order_by('-created_at')[:5]
        
        return context


@cache_function(timeout=60*15)  # 15 minutes
@log_queries
def get_dashboard_data():
    """
    Get dashboard data for the main dashboard view.
    This function is cached to avoid repeated database queries.
    Optimized to reduce database queries.
    
    Returns:
        dict: Dashboard statistics
    """
    logger.debug("Calculating dashboard statistics...")
    stats = {}
    now = timezone.now()
    
    # Determine date ranges for efficient querying
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    thirty_days_ago = now - timedelta(days=30)
    
    # Summary statistics - use efficient counters
    customer_count = Customer.objects.filter(is_active=True).count()
    product_count = Product.objects.filter(status='available').count()
    
    # Get order data in a single query with annotations
    orders_data = Order.objects.aggregate(
        total_count=Count('id'),
        total_revenue=Sum('total_amount', filter=Q(status__in=['completed', 'delivered'])),
        current_month_count=Count('id', filter=Q(created_at__gte=start_of_month)),
        current_month_revenue=Sum('total_amount', 
                               filter=Q(created_at__gte=start_of_month, 
                                       status__in=['completed', 'delivered'])),
        prev_month_count=Count('id', filter=Q(created_at__gte=prev_month_start, 
                                            created_at__lt=start_of_month)),
        prev_month_revenue=Sum('total_amount', 
                             filter=Q(created_at__gte=prev_month_start,
                                     created_at__lt=start_of_month,
                                     status__in=['completed', 'delivered'])),
        thirty_day_count=Count('id', filter=Q(created_at__gte=thirty_days_ago)),
        thirty_day_revenue=Sum('total_amount', 
                             filter=Q(created_at__gte=thirty_days_ago,
                                     status__in=['completed', 'delivered']))
    )
    
    # Populate stats with query results
    stats['total_customers'] = customer_count
    stats['total_products'] = product_count
    stats['total_orders'] = orders_data['total_count']
    stats['total_revenue'] = orders_data['total_revenue'] or 0
    stats['monthly_orders'] = orders_data['current_month_count']
    stats['monthly_revenue'] = orders_data['current_month_revenue'] or 0
    stats['prev_month_orders'] = orders_data['prev_month_count']
    stats['prev_month_revenue'] = orders_data['prev_month_revenue'] or 0
    stats['last_30d_orders_count'] = orders_data['thirty_day_count']
    stats['last_30d_revenue'] = orders_data['thirty_day_revenue'] or 0
    
    # Calculate percentage changes
    if stats['prev_month_orders'] > 0:
        stats['monthly_orders_change'] = (
            (stats['monthly_orders'] - stats['prev_month_orders']) / 
            stats['prev_month_orders'] * 100
        )
    else:
        stats['monthly_orders_change'] = 100  # If no previous orders, show as 100% increase
    
    if stats['prev_month_revenue'] > 0:
        stats['monthly_revenue_change'] = (
            (stats['monthly_revenue'] - stats['prev_month_revenue']) / 
            stats['prev_month_revenue'] * 100
        )
    else:
        stats['monthly_revenue_change'] = 100  # If no previous revenue, show as 100% increase
    
    # Top customers - optimized query
    top_customers = Customer.objects.annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total_amount', default=0)
    ).filter(order_count__gt=0).order_by('-total_spent')[:5]
    
    stats['top_customers'] = list(top_customers.values(
        'id', 'name', 'company_name', 'email', 'order_count', 'total_spent'
    ))
    
    # Top products - optimized query with select_related
    top_products = OrderItem.objects.select_related('product').values(
        'product__name', 'product_id'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('unit_price') * F('quantity'), output_field=DecimalField())
    ).order_by('-quantity_sold')[:5]
    
    stats['top_products'] = list(top_products)
    
    return stats


@cache_function(timeout=60*60*2)  # 2 hours
@log_queries
def get_chart_data(chart_type, period='month'):
    """
    Get chart data for the dashboard.
    
    Args:
        chart_type: Type of chart (sales, products, etc.)
        period: Time period (day, week, month, year)
        
    Returns:
        dict: Chart data
    """
    logger.debug(f"Generating chart data for {chart_type} ({period})...")
    
    if chart_type == 'sales':
        return _get_sales_chart_data(period)
    elif chart_type == 'products':
        return _get_products_chart_data(period)
    
    return {}


@log_queries
def _get_sales_chart_data(period):
    """
    Get sales chart data.
    Optimized to reduce the number of database queries.
    
    Args:
        period: Time period (day, week, month, year)
        
    Returns:
        dict: Sales chart data
    """
    now = timezone.now()
    from django.db.models.functions import TruncHour, TruncDay, TruncMonth
    
    # Determine date range and trunc function based on period
    if period == 'day':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_format = '%H:%M'
        trunc_function = TruncHour('created_at')
        date_field = 'hour'
    elif period == 'week':
        start_date = now - timedelta(days=7)
        date_format = '%a'
        trunc_function = TruncDay('created_at')
        date_field = 'day'
    elif period == 'year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        date_format = '%b'
        trunc_function = TruncMonth('created_at')
        date_field = 'month'
    else:  # month (default)
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        date_format = '%d'
        trunc_function = TruncDay('created_at')
        date_field = 'day'
    
    # Use Django ORM's aggregation and annotation to get all data in a single query
    # Group by time period and calculate order count and revenue
    grouped_data = Order.objects.filter(
        created_at__gte=start_date
    ).annotate(
        period=trunc_function
    ).values(
        'period'
    ).annotate(
        order_count=Count('id'),
        revenue_sum=Sum('total_amount')
    ).order_by('period')
    
    # Convert to dictionary for easier lookup
    period_data = {item['period']: {
        'count': item['order_count'],
        'revenue': item['revenue_sum'] or 0
    } for item in grouped_data}
    
    # Prepare data structure
    data = {
        'labels': [],
        'datasets': [
            {
                'label': 'Revenue',
                'data': []
            },
            {
                'label': 'Orders',
                'data': []
            }
        ]
    }
    
    # Generate periods list based on selected time range
    if period == 'day':
        periods = [start_date + timedelta(hours=hour) for hour in range(24)]
    elif period == 'week':
        periods = [start_date + timedelta(days=day) for day in range(7)]
    elif period == 'year':
        periods = [start_date.replace(month=month+1) for month in range(12)]
    else:  # month
        days_in_month = (start_date.replace(month=start_date.month % 12 + 1, day=1) - timedelta(days=1)).day
        periods = [start_date.replace(day=day+1) for day in range(days_in_month)]
    
    # Fill data for each period
    for period_date in periods:
        # Add label
        data['labels'].append(period_date.strftime(date_format))
        
        # Add data for this period
        if period_date in period_data:
            data['datasets'][0]['data'].append(float(period_data[period_date]['revenue']))
            data['datasets'][1]['data'].append(period_data[period_date]['count'])
        else:
            # No data for this period
            data['datasets'][0]['data'].append(0)
            data['datasets'][1]['data'].append(0)
    
    return data


@log_queries
def _get_products_chart_data(period):
    """
    Get products chart data.
    Optimized with select_related to reduce queries.
    
    Args:
        period: Time period (day, week, month, year)
        
    Returns:
        dict: Products chart data
    """
    now = timezone.now()
    
    # Determine date range based on period
    if period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # month (default)
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get top products by sales in time range
    # Use select_related to optimize query
    top_products = OrderItem.objects.select_related(
        'product', 'order'
    ).filter(
        order__created_at__gte=start_date
    ).values(
        'product__name'
    ).annotate(
        quantity_sold=Sum('quantity')
    ).order_by('-quantity_sold')[:10]
    
    # Prepare data structure
    data = {
        'labels': [p['product__name'] for p in top_products],
        'datasets': [
            {
                'label': 'Units Sold',
                'data': [p['quantity_sold'] for p in top_products]
            }
        ]
    }
    
    return data