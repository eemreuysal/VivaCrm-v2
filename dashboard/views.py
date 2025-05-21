"""
Dashboard views for VivaCRM v2.

This module provides the views and related utility functions for the dashboard page.
It includes components for displaying key metrics, charts, and summary data.
The dashboard is optimized with caching to reduce database load.
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, F, DecimalField, Q, Value, CharField, Avg
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
import logging
import json

from customers.models import Customer
from products.models import Product, Category
from orders.models import Order, OrderItem
from admin_panel.models import SystemSettings
from core.query_optimizer import log_queries, optimize_queryset
from .cache_helpers import (
    get_cached_dashboard_stats, 
    get_cached_chart_data,
    get_cached_low_stock_products
)

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view showing key business metrics and visualizations.
    
    This is the primary dashboard view that renders the full dashboard page.
    It doesn't load any data directly, but rather sets up the page structure
    for content to be loaded via HTMX.
    """
    template_name = "dashboard/dashboard.html"
    
    def get_context_data(self, **kwargs):
        """Provides minimal context data for initial page load."""
        context = super().get_context_data(**kwargs)
        
        # Get system settings for dashboard config
        context['system_settings'] = self._get_system_settings()
        
        return context
    
    def _get_system_settings(self):
        """Get system settings for dashboard configuration."""
        return {
            'currency_symbol': SystemSettings.get_setting('currency_symbol', default='₺'),
            'refresh_interval': SystemSettings.get_setting('dashboard_refresh', default='0')
        }


class DashboardContentView(LoginRequiredMixin, TemplateView):
    """
    Dashboard content view that handles partial content updates.
    
    This view renders only the dashboard content (stats, charts, tables),
    and is designed to be loaded via HTMX for dynamic updates.
    """
    template_name = "dashboard/partials/_dashboard_content.html"
    
    @log_queries
    def get_context_data(self, **kwargs):
        """
        Prepare all the data needed for the dashboard content.
        Uses caching for optimal performance.
        """
        context = super().get_context_data(**kwargs)
        
        # Get period from request
        period = self.request.GET.get('period', 'month')
        
        # Get date ranges based on period
        date_ranges = self._get_date_ranges(period)
        context.update(date_ranges)
        
        # Add period description for UI
        context['period_description'] = self._get_period_description(period, date_ranges)
        
        # Get cached dashboard stats
        start_date_str = date_ranges['start_date'].strftime('%Y-%m-%d') if date_ranges['start_date'] else None
        end_date_str = date_ranges['end_date'].strftime('%Y-%m-%d') if date_ranges['end_date'] else None
        
        # Check if forced refresh is requested
        refresh_cache = self.request.GET.get('refresh', 'false') == 'true'
        
        # Get dashboard statistics
        dashboard_stats = get_cached_dashboard_stats(
            refresh=refresh_cache,
            start_date=start_date_str,
            end_date=end_date_str
        )
        context.update(dashboard_stats)
        
        # Calculate and add trends data
        self._add_trends_data(context, date_ranges)
        
        # Add chart data
        chart_data = self._get_chart_data(date_ranges, period)
        context.update(chart_data)
        
        # Add recent orders and low stock products
        context['recent_orders'] = self._get_recent_orders(date_ranges['start_date'], date_ranges['end_date'])
        context['low_stock_products'] = get_cached_low_stock_products(limit=5)
        
        return context
    
    def _get_date_ranges(self, period):
        """
        Calculate date ranges based on the specified period.
        
        Args:
            period: Period filter (today, week, month, year, custom)
            
        Returns:
            dict: Dictionary with date range values
        """
        today = timezone.now().date()
        date_ranges = {
            'period': period,
            'start_date': None,
            'end_date': None,
            'previous_start_date': None,
            'previous_end_date': None
        }
        
        # Set appropriate date ranges based on period
        if period == 'today':
            date_ranges['start_date'] = today
            date_ranges['end_date'] = today
            date_ranges['previous_start_date'] = today - timedelta(days=1)
            date_ranges['previous_end_date'] = today - timedelta(days=1)
        
        elif period == 'week':
            # Start of current week (Monday)
            date_ranges['start_date'] = today - timedelta(days=today.weekday())
            date_ranges['end_date'] = today
            # Previous week
            date_ranges['previous_start_date'] = date_ranges['start_date'] - timedelta(days=7)
            date_ranges['previous_end_date'] = date_ranges['start_date'] - timedelta(days=1)
        
        elif period == 'month':
            # Start of current month
            date_ranges['start_date'] = today.replace(day=1)
            date_ranges['end_date'] = today
            # Previous month
            if today.month == 1:
                prev_month = today.replace(year=today.year-1, month=12, day=1)
            else:
                prev_month = today.replace(month=today.month-1, day=1)
            
            date_ranges['previous_start_date'] = prev_month
            # Last day of previous month
            last_day = date_ranges['start_date'] - timedelta(days=1)
            date_ranges['previous_end_date'] = last_day
        
        elif period == 'year':
            # Start of current year
            date_ranges['start_date'] = today.replace(month=1, day=1)
            date_ranges['end_date'] = today
            # Previous year
            date_ranges['previous_start_date'] = today.replace(year=today.year-1, month=1, day=1) 
            date_ranges['previous_end_date'] = today.replace(year=today.year-1, month=12, day=31)
        
        elif period == 'custom':
            # Custom date range from request
            self._handle_custom_date_range(date_ranges)
        
        else:
            # Default to month if period is invalid
            date_ranges = self._get_date_ranges('month')
        
        return date_ranges
    
    def _handle_custom_date_range(self, date_ranges):
        """
        Handle custom date range from request parameters.
        
        Args:
            date_ranges: Dictionary to update with custom date range values
        """
        # Get custom date range from request parameters
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                # Parse date strings to date objects
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                # Validate date range
                if start_date > end_date:
                    # Invalid range, fall back to month
                    logger.warning("Invalid custom date range: start_date > end_date")
                    date_ranges.update(self._get_date_ranges('month'))
                    return
                
                # Set custom date range
                date_ranges['start_date'] = start_date
                date_ranges['end_date'] = end_date
                
                # Calculate previous period for comparison
                # (Same duration, immediately before the selected period)
                days_diff = (end_date - start_date).days
                date_ranges['previous_start_date'] = start_date - timedelta(days=days_diff+1)
                date_ranges['previous_end_date'] = start_date - timedelta(days=1)
                
            except ValueError as e:
                # Date parsing failed, fall back to month
                logger.warning(f"Failed to parse custom date range: {e}")
                date_ranges.update(self._get_date_ranges('month'))
        else:
            # No custom dates provided, fall back to month
            date_ranges.update(self._get_date_ranges('month'))
    
    def _get_period_description(self, period, date_ranges):
        """
        Generate a human-readable description of the selected time period.
        
        Args:
            period: The period type (today, week, month, year, custom)
            date_ranges: Dictionary with date range information
            
        Returns:
            str: Human-readable period description
        """
        if period == 'today':
            return f"{date_ranges['start_date'].strftime('%d %b %Y')}"
        elif period == 'custom':
            return f"{date_ranges['start_date'].strftime('%d %b %Y')} - {date_ranges['end_date'].strftime('%d %b %Y')}"
        elif period == 'week':
            return f"{date_ranges['start_date'].strftime('%d %b')} - {date_ranges['end_date'].strftime('%d %b %Y')}"
        elif period == 'month':
            return date_ranges['start_date'].strftime('%B %Y')
        elif period == 'year':
            return date_ranges['start_date'].strftime('%Y')
        
        return ""
    
    def _add_trends_data(self, context, date_ranges):
        """
        Calculate and add trend data to the context.
        Uses more efficient aggregated queries.
        
        Args:
            context: Context dictionary to update
            date_ranges: Dictionary with date range information
        """
        if not (date_ranges['previous_start_date'] and date_ranges['previous_end_date']):
            # Cannot calculate trends without previous period
            context.update({
                'order_trend': 0,
                'revenue_trend': 0,
                'customer_trend': 0,
                'product_trend': 0
            })
            return
        
        # Calculate order and revenue trends in a single query
        order_data = self._calculate_order_trends(
            date_ranges['start_date'], 
            date_ranges['end_date'],
            date_ranges['previous_start_date'], 
            date_ranges['previous_end_date']
        )
        
        # Calculate customer trend
        customer_trend = self._calculate_customer_trend(
            date_ranges['start_date'], 
            date_ranges['end_date'],
            date_ranges['previous_start_date'], 
            date_ranges['previous_end_date']
        )
        
        # Calculate product trend
        product_trend = self._calculate_product_trend(
            date_ranges['start_date'], 
            date_ranges['end_date'],
            date_ranges['previous_start_date'], 
            date_ranges['previous_end_date']
        )
        
        # Add all trends to context
        context.update({
            'order_trend': order_data['order_trend'],
            'revenue_trend': order_data['revenue_trend'],
            'customer_trend': customer_trend,
            'product_trend': product_trend
        })
    
    def _calculate_order_trends(self, start_date, end_date, prev_start_date, prev_end_date):
        """
        Calculate order and revenue trends in a single efficient query.
        Uses Django ORM's aggregation features.
        
        Args:
            start_date: Current period start date
            end_date: Current period end date
            prev_start_date: Previous period start date
            prev_end_date: Previous period end date
            
        Returns:
            dict: Dictionary with order and revenue trends
        """
        from django.db.models import Q, Count, Sum, Case, When, IntegerField, F
        
        # Query for current and previous periods in one go
        result = {}
        
        # Current period stats
        current_stats = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).aggregate(
            order_count=Count('id'),
            revenue=Coalesce(Sum('total_amount', filter=Q(
                status__in=['completed', 'delivered']
            )), Value(0), output_field=DecimalField())
        )
        
        # Previous period stats
        prev_stats = Order.objects.filter(
            created_at__date__gte=prev_start_date,
            created_at__date__lte=prev_end_date
        ).aggregate(
            order_count=Count('id'),
            revenue=Coalesce(Sum('total_amount', filter=Q(
                status__in=['completed', 'delivered']
            )), Value(0), output_field=DecimalField())
        )
        
        # Calculate trends
        current_orders = current_stats['order_count'] or 0
        prev_orders = prev_stats['order_count'] or 0
        
        current_revenue = current_stats['revenue'] or 0
        prev_revenue = prev_stats['revenue'] or 0
        
        # Calculate percentage changes
        result['order_trend'] = self._calculate_percentage_change(current_orders, prev_orders)
        result['revenue_trend'] = self._calculate_percentage_change(current_revenue, prev_revenue)
        
        return result
    
    def _calculate_customer_trend(self, start_date, end_date, prev_start_date, prev_end_date):
        """
        Calculate customer trend.
        
        Args:
            start_date: Current period start date
            end_date: Current period end date
            prev_start_date: Previous period start date
            prev_end_date: Previous period end date
            
        Returns:
            float: Customer trend percentage
        """
        # Current period customer count
        current_customers = Customer.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            is_active=True
        ).count()
        
        # Previous period customer count
        prev_customers = Customer.objects.filter(
            created_at__date__gte=prev_start_date,
            created_at__date__lte=prev_end_date,
            is_active=True
        ).count()
        
        return self._calculate_percentage_change(current_customers, prev_customers)
    
    def _calculate_product_trend(self, start_date, end_date, prev_start_date, prev_end_date):
        """
        Calculate product trend.
        
        Args:
            start_date: Current period start date
            end_date: Current period end date
            prev_start_date: Previous period start date
            prev_end_date: Previous period end date
            
        Returns:
            float: Product trend percentage
        """
        # Current period product count
        current_products = Product.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='available'
        ).count()
        
        # Previous period product count
        prev_products = Product.objects.filter(
            created_at__date__gte=prev_start_date,
            created_at__date__lte=prev_end_date,
            status='available'
        ).count()
        
        return self._calculate_percentage_change(current_products, prev_products)
    
    def _calculate_percentage_change(self, current_value, previous_value):
        """
        Calculate percentage change between two values.
        
        Args:
            current_value: Current period value
            previous_value: Previous period value
            
        Returns:
            float: Percentage change
        """
        if previous_value > 0:
            return ((current_value - previous_value) / previous_value * 100)
        elif current_value > 0:
            return 100  # If no previous value but current value exists, show as 100% increase
        else:
            return 0  # If both are 0, no change
    
    def _get_chart_data(self, date_ranges, period='month'):
        """
        Get chart data for the dashboard using the caching system.
        
        Args:
            date_ranges: Date range dictionary
            period: Time period (day, week, month, year, custom)
            
        Returns:
            dict: Dictionary with chart data formatted for templates
        """
        # Use the period to get appropriate chart data from cache
        chart_data = {}
        
        # Check if cached chart data refresh is requested
        refresh_cache = self.request.GET.get('refresh', 'false') == 'true'
        
        # Get JSON data for charts
        sales_data = get_cached_chart_data('sales', period, refresh=refresh_cache)
        products_data = get_cached_chart_data('products', period, refresh=refresh_cache)
        orders_data = get_cached_chart_data('orders', period, refresh=refresh_cache)
        
        # Format for template use - sales chart
        if sales_data and 'labels' in sales_data and 'datasets' in sales_data and sales_data['datasets']:
            chart_data['sales_labels'] = json.dumps(sales_data['labels'])
            chart_data['sales_data'] = json.dumps(sales_data['datasets'])
        else:
            chart_data['sales_labels'] = '[]'
            chart_data['sales_data'] = '[]'
        
        # Format for template use - category chart
        if products_data and 'labels' in products_data and 'datasets' in products_data and products_data['datasets']:
            chart_data['category_labels'] = json.dumps(products_data['labels'])
            chart_data['category_data'] = json.dumps(products_data['datasets'])
        else:
            chart_data['category_labels'] = '[]'
            chart_data['category_data'] = '[]'
        
        # Format for template use - orders chart
        if orders_data and 'labels' in orders_data and 'datasets' in orders_data and orders_data['datasets']:
            chart_data['orders_labels'] = json.dumps(orders_data['labels'])
            chart_data['orders_data'] = json.dumps(orders_data['datasets'])
        else:
            chart_data['orders_labels'] = '[]'
            chart_data['orders_data'] = '[]'
        
        return chart_data
    
    @optimize_queryset
    def _get_recent_orders(self, start_date, end_date):
        """
        Get recent orders for the dashboard, optimized with select_related.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            QuerySet: Recent orders
        """
        # Query recent orders with efficient eager loading
        orders_query = Order.objects.select_related(
            'customer', 'owner'
        ).order_by('-created_at')
        
        # Apply date filters if provided
        if start_date and end_date:
            orders_query = orders_query.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
        
        # Limit to last 5 orders
        return orders_query[:5]