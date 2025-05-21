"""
API views for dashboard data.

This module contains API endpoints for retrieving dashboard data in JSON format.
"""

from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..cache_helpers import (
    get_cached_dashboard_stats,
    get_cached_chart_data,
    get_cached_low_stock_products
)
from ..views import DashboardContentView


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    API endpoint for retrieving dashboard statistics data.
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse: Dashboard statistics in JSON format
    """
    # Get period and date range information from request
    period = request.GET.get('period', 'month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Check if forced refresh is requested
    refresh = request.GET.get('refresh', 'false') == 'true'
    
    # Retrieve cached dashboard statistics
    stats = get_cached_dashboard_stats(
        refresh=refresh,
        start_date=start_date,
        end_date=end_date
    )
    
    # Calculate additional trends if needed
    if 'order_trend' not in stats:
        # Create a temporary view instance to calculate trends
        view = DashboardContentView()
        date_ranges = view._get_date_ranges(period)
        
        # Add trends to stats
        view._add_trends_data(stats, date_ranges)
    
    return JsonResponse(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_chart_data(request, chart_type):
    """
    API endpoint for retrieving dashboard chart data.
    
    Args:
        request: HTTP request object
        chart_type: Type of chart data to retrieve (sales, products, orders)
        
    Returns:
        JsonResponse: Chart data in JSON format
    """
    # Get period from request
    period = request.GET.get('period', 'month')
    
    # Check if forced refresh is requested
    refresh = request.GET.get('refresh', 'false') == 'true'
    
    # Retrieve cached chart data
    chart_data = get_cached_chart_data(chart_type, period, refresh=refresh)
    
    # If no chart data found, return empty structure
    if not chart_data:
        chart_data = {
            'labels': [],
            'datasets': []
        }
    
    return JsonResponse(chart_data)


class DashboardApiView(DashboardContentView):
    """
    API view for all dashboard data, inherits from DashboardContentView.
    
    This view returns all dashboard data in JSON format for RESTful API usage.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for dashboard API.
        
        Args:
            request: HTTP request object
            
        Returns:
            JsonResponse: Complete dashboard data in JSON format
        """
        # Get context data from parent class
        context = self.get_context_data(**kwargs)
        
        # Convert appropriate values to JSON-serializable format
        result = {
            'period': context.get('period', 'month'),
            'period_description': context.get('period_description', ''),
            'date_ranges': {
                'start_date': context.get('start_date').isoformat() if context.get('start_date') else None,
                'end_date': context.get('end_date').isoformat() if context.get('end_date') else None,
            },
            'stats': {
                'total_orders': context.get('total_orders', 0),
                'total_revenue': float(context.get('total_revenue', 0)),
                'total_customers': context.get('total_customers', 0),
                'total_products': context.get('total_products', 0),
                'order_trend': context.get('order_trend', 0),
                'revenue_trend': context.get('revenue_trend', 0),
                'customer_trend': context.get('customer_trend', 0),
                'product_trend': context.get('product_trend', 0),
            },
            'charts': {
                'sales': {
                    'labels': context.get('sales_labels', '[]'),
                    'datasets': context.get('sales_data', '[]'),
                },
                'categories': {
                    'labels': context.get('category_labels', '[]'),
                    'datasets': context.get('category_data', '[]'),
                },
                'orders': {
                    'labels': context.get('orders_labels', '[]'),
                    'datasets': context.get('orders_data', '[]'),
                }
            },
        }
        
        # Add low stock products data
        low_stock_products = []
        for product in context.get('low_stock_products', []):
            low_stock_products.append({
                'id': str(product.id),
                'name': product.name,
                'sku': product.sku,
                'stock_quantity': product.stock,
                'threshold_stock': product.threshold_stock,
                'status': 'out_of_stock' if product.stock == 0 else 'low_stock'
            })
        
        result['low_stock_products'] = low_stock_products
        
        # Add recent orders data
        recent_orders = []
        for order in context.get('recent_orders', []):
            recent_orders.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'customer_name': order.customer.name,
                'created_at': order.created_at.isoformat(),
                'total_amount': float(order.total_amount),
                'status': order.status,
                'status_display': order.get_status_display()
            })
        
        result['recent_orders'] = recent_orders
        
        return JsonResponse(result)