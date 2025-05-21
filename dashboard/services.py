"""
Dashboard data services.

This module provides service functions for retrieving and processing dashboard data.
It serves as a separate service layer to isolate business logic from views.
"""

import logging
from datetime import datetime, timedelta

from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, Q, Window
from django.db.models.functions import TruncDay, TruncMonth

from products.models import Product, StockMovement, Category
from orders.models import Order, OrderItem
from customers.models import Customer
from invoices.models import Invoice

logger = logging.getLogger(__name__)


def get_dashboard_data(start_date=None, end_date=None):
    """
    Get dashboard statistics data.
    
    Collects and aggregates data from various models to provide
    statistics for the dashboard.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        dict: Dashboard statistics
    """
    logger.debug(f"Getting dashboard data for period: {start_date} to {end_date}")
    
    # Parse date strings to datetime objects if provided
    start_datetime = None
    end_datetime = None
    
    if start_date:
        try:
            start_datetime = timezone.make_aware(
                datetime.strptime(start_date, '%Y-%m-%d')
            )
        except (ValueError, TypeError):
            logger.warning(f"Invalid start_date format: {start_date}")
    
    if end_date:
        try:
            # Set end_datetime to the end of the day
            end_datetime = timezone.make_aware(
                datetime.strptime(end_date, '%Y-%m-%d').replace(
                    hour=23, minute=59, second=59
                )
            )
        except (ValueError, TypeError):
            logger.warning(f"Invalid end_date format: {end_date}")
    
    # Filter queryset by date range if specified
    orders_filter = Q()
    if start_datetime:
        orders_filter &= Q(created_at__gte=start_datetime)
    if end_datetime:
        orders_filter &= Q(created_at__lte=end_datetime)
    
    # Order statistics
    orders = Order.objects.filter(orders_filter)
    completed_orders = orders.filter(status='completed')
    
    # Query for aggregated statistics
    order_count = orders.count()
    completed_order_count = completed_orders.count()
    total_sales = completed_orders.aggregate(
        total=Sum('total_amount', default=0)
    )['total'] or 0
    
    # Customer statistics
    if start_datetime and end_datetime:
        new_customers = Customer.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        ).count()
    else:
        new_customers = 0  # Default, can be calculated differently if needed
    
    # Product statistics
    low_stock_products = Product.objects.filter(
        stock__lt=F('threshold_stock')
    ).count()
    
    # Top selling products
    top_selling_products = []
    if completed_orders:
        # Get product IDs and their quantities from OrderItems
        top_selling_product_ids = OrderItem.objects.filter(
            order__in=completed_orders
        ).values('product').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:5]
        
        # Get actual product objects
        if top_selling_product_ids:
            product_ids = [item['product'] for item in top_selling_product_ids]
            products = {
                p.id: p for p in Product.objects.filter(id__in=product_ids)
            }
            top_selling_products = [
                {
                    'id': item['product'],
                    'name': products[item['product']].name if item['product'] in products else 'Unknown',
                    'quantity': item['total_quantity']
                }
                for item in top_selling_product_ids
            ]
    
    # Assemble the result
    result = {
        'start_date': start_date,
        'end_date': end_date,
        'order_count': order_count,
        'completed_order_count': completed_order_count,
        'total_sales': total_sales,
        'low_stock_products': low_stock_products,
        'new_customers': new_customers,
        'top_selling_products': top_selling_products,
    }
    
    # Calculate conversion rate
    if order_count > 0:
        result['conversion_rate'] = round((completed_order_count / order_count) * 100, 2)
    else:
        result['conversion_rate'] = 0
    
    # Calculate average order value
    if completed_order_count > 0:
        result['average_order_value'] = round(total_sales / completed_order_count, 2)
    else:
        result['average_order_value'] = 0
    
    logger.debug(f"Dashboard data collected successfully with {order_count} orders")
    return result


def get_chart_data(chart_type, period):
    """
    Get chart data for the specified type and period.
    
    Args:
        chart_type: Type of chart (sales, products, orders, customers)
        period: Time period (day, week, month, year, custom)
        
    Returns:
        dict: Chart data with labels and datasets
    """
    logger.debug(f"Getting chart data for type: {chart_type}, period: {period}")
    
    # Determine date range based on period
    now = timezone.now()
    start_date = None
    
    if period == 'day':
        start_date = now - timedelta(days=1)
        trunc_function = TruncDay
    elif period == 'week':
        start_date = now - timedelta(days=7)
        trunc_function = TruncDay
    elif period == 'month':
        start_date = now - timedelta(days=30)
        trunc_function = TruncDay
    elif period == 'year':
        start_date = now - timedelta(days=365)
        trunc_function = TruncMonth
    else:
        # Default to month
        start_date = now - timedelta(days=30)
        trunc_function = TruncDay
    
    if not start_date:
        return {'labels': [], 'datasets': []}
    
    # Process different chart types
    if chart_type == 'sales':
        # Get sales data grouped by day/month
        sales_data = Order.objects.filter(
            created_at__gte=start_date,
            status='completed'
        ).annotate(
            date=trunc_function('created_at')
        ).values('date').annotate(
            total=Sum('total_amount')
        ).order_by('date')
        
        # Format data for chart
        dates = []
        amounts = []
        
        for entry in sales_data:
            # Format date based on period
            if period == 'year':
                date_str = entry['date'].strftime('%b %Y')  # Jan 2023
            else:
                date_str = entry['date'].strftime('%d %b')  # 01 Jan
            
            dates.append(date_str)
            amounts.append(float(entry['total']) if entry['total'] else 0)
        
        return {
            'labels': dates,
            'datasets': [{
                'label': 'Sales',
                'data': amounts,
                'borderColor': '#22c55e',
                'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                'borderWidth': 2,
                'fill': True
            }]
        }
    
    elif chart_type == 'orders':
        # Get order counts grouped by day/month
        order_data = Order.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=trunc_function('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Format data for chart
        dates = []
        counts = []
        
        for entry in order_data:
            # Format date based on period
            if period == 'year':
                date_str = entry['date'].strftime('%b %Y')
            else:
                date_str = entry['date'].strftime('%d %b')
            
            dates.append(date_str)
            counts.append(entry['count'])
        
        return {
            'labels': dates,
            'datasets': [{
                'label': 'Orders',
                'data': counts,
                'borderColor': '#0ea5e9',
                'backgroundColor': 'rgba(14, 165, 233, 0.1)',
                'borderWidth': 2,
                'fill': True
            }]
        }
    
    elif chart_type == 'products':
        # Get top product categories by sales
        category_data = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__status='completed'
        ).values(
            'product__category__name'
        ).annotate(
            total=Sum('quantity')
        ).order_by('-total')[:8]  # Limit to top 8 categories
        
        # Format data for chart
        categories = []
        quantities = []
        
        for entry in category_data:
            category_name = entry['product__category__name'] or 'Uncategorized'
            categories.append(category_name)
            quantities.append(entry['total'])
        
        return {
            'labels': categories,
            'datasets': [{
                'label': 'Sales by Category',
                'data': quantities,
                'backgroundColor': [
                    '#22c55e', '#0ea5e9', '#f59e0b', '#ef4444',
                    '#8b5cf6', '#ec4899', '#14b8a6', '#6366f1'
                ],
                'borderWidth': 0
            }]
        }
    
    elif chart_type == 'customers':
        # Get new customers by day/month
        customer_data = Customer.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=trunc_function('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Format data for chart
        dates = []
        counts = []
        
        for entry in customer_data:
            # Format date based on period
            if period == 'year':
                date_str = entry['date'].strftime('%b %Y')
            else:
                date_str = entry['date'].strftime('%d %b')
            
            dates.append(date_str)
            counts.append(entry['count'])
        
        return {
            'labels': dates,
            'datasets': [{
                'label': 'New Customers',
                'data': counts,
                'borderColor': '#f59e0b',
                'backgroundColor': 'rgba(245, 158, 11, 0.1)',
                'borderWidth': 2,
                'fill': True
            }]
        }
    
    # Default empty response
    return {'labels': [], 'datasets': []}


def get_recent_orders(limit=10):
    """
    Get recent orders for the dashboard.
    
    Args:
        limit: Maximum number of orders to return
        
    Returns:
        QuerySet: Recent orders
    """
    return Order.objects.select_related(
        'customer'
    ).prefetch_related(
        'items'
    ).order_by(
        '-created_at'
    )[:limit]


def get_low_stock_products(limit=10, threshold_ratio=1.0):
    """
    Get products with low stock for the dashboard.
    
    Args:
        limit: Maximum number of products to return
        threshold_ratio: Ratio to multiply the threshold by (default 1.0)
        
    Returns:
        QuerySet: Low stock products
    """
    return Product.objects.filter(
        status='available',
        stock__lt=F('threshold_stock') * threshold_ratio
    ).select_related(
        'category'
    ).order_by(
        'stock'
    )[:limit]