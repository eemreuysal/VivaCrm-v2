from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, F, DecimalField, Q, Value, CharField, Case, When
from django.db.models.functions import TruncDate, TruncMonth
from datetime import datetime, timedelta
from django.utils import timezone
import calendar

from customers.models import Customer
from products.models import Product, Category
from orders.models import Order, OrderItem
from invoices.models import Invoice

from .serializers import (
    DashboardSummarySerializer, RecentOrderSerializer, TopCustomerSerializer,
    TopProductSerializer, LowStockProductSerializer, SalesChartDataSerializer,
    ProductCategoryChartSerializer, OrderStatusChartSerializer,
    CustomerTypeChartSerializer
)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
    """
    API endpoint for dashboard summary statistics.
    """
    # Current time and date ranges
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)
    
    # Summary statistics
    total_customers = Customer.objects.filter(is_active=True).count()
    total_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.all().count()
    
    # Revenue
    revenue = Order.objects.filter(
        status__in=['completed', 'delivered']
    ).aggregate(Sum('total_amount'))
    total_revenue = revenue['total_amount__sum'] or 0
    
    # Current month statistics
    month_orders = Order.objects.filter(created_at__gte=start_of_month)
    monthly_orders = month_orders.count()
    month_revenue = month_orders.filter(
        status__in=['completed', 'delivered']
    ).aggregate(Sum('total_amount'))
    monthly_revenue = month_revenue['total_amount__sum'] or 0
    
    # Last 30 days orders
    last_30d_orders_count = Order.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # Build response data
    data = {
        'total_customers': total_customers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'monthly_orders': monthly_orders,
        'monthly_revenue': monthly_revenue,
        'last_30d_orders_count': last_30d_orders_count
    }
    
    serializer = DashboardSummarySerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recent_orders(request):
    """
    API endpoint for recent orders.
    """
    # Get only 5 most recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    serializer = RecentOrderSerializer(recent_orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def top_customers(request):
    """
    API endpoint for top customers.
    """
    top_customers = Customer.objects.annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total_amount', default=0)
    ).filter(order_count__gt=0).order_by('-total_spent')[:5]
    
    serializer = TopCustomerSerializer(top_customers, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def top_products(request):
    """
    API endpoint for top products.
    """
    top_products = OrderItem.objects.values(
        'product__name', 'product__id'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
    ).order_by('-quantity_sold')[:5]
    
    serializer = TopProductSerializer(top_products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def low_stock_products(request):
    """
    API endpoint for low stock products.
    """
    low_stock_products = Product.objects.filter(
        is_active=True, 
        stock__lte=F('threshold_stock'),
        is_physical=True
    ).order_by('stock')[:5]
    
    serializer = LowStockProductSerializer(low_stock_products, many=True)
    return Response(serializer.data)


class SalesChartView(APIView):
    """
    API endpoint for sales chart data.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        period = request.query_params.get('period', 'daily')
        days = int(request.query_params.get('days', 30))
        
        # Limit days to reasonable values
        if days > 365:
            days = 365
        elif days < 7:
            days = 7
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        if period == 'monthly':
            # Monthly aggregation
            sales_data = Order.objects.filter(
                created_at__gte=start_date
            ).annotate(
                date=TruncMonth('created_at')
            ).values('date').annotate(
                orders=Count('id'),
                revenue=Sum('total_amount', default=0)
            ).order_by('date')
        else:
            # Daily aggregation (default)
            sales_data = Order.objects.filter(
                created_at__gte=start_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                orders=Count('id'),
                revenue=Sum('total_amount', default=0)
            ).order_by('date')
        
        serializer = SalesChartDataSerializer(sales_data, many=True)
        return Response(serializer.data)


class ProductCategoryChartView(APIView):
    """
    API endpoint for product category distribution chart.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Count products by category
        category_data = Product.objects.values(
            'category__name'
        ).annotate(
            category=F('category__name'),
            product_count=Count('id')
        ).order_by('-product_count')
        
        # Handle products without a category
        for item in category_data:
            if item['category'] is None:
                item['category'] = 'Uncategorized'
        
        serializer = ProductCategoryChartSerializer(category_data, many=True)
        return Response(serializer.data)


class OrderStatusChartView(APIView):
    """
    API endpoint for order status distribution chart.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Count orders by status
        status_data = Order.objects.values(
            'status'
        ).annotate(
            status_display=Case(
                *[When(status=k, then=Value(v)) for k, v in dict(Order.STATUS_CHOICES).items()],
                output_field=CharField()
            ),
            order_count=Count('id')
        ).order_by('-order_count')
        
        serializer = OrderStatusChartSerializer(status_data, many=True)
        return Response(serializer.data)


class CustomerTypeChartView(APIView):
    """
    API endpoint for customer type distribution chart.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Count customers by type
        type_data = Customer.objects.values(
            'type'
        ).annotate(
            type_display=Case(
                *[When(type=k, then=Value(v)) for k, v in dict(Customer.CUSTOMER_TYPE_CHOICES).items()],
                output_field=CharField()
            ),
            customer_count=Count('id')
        ).order_by('-customer_count')
        
        serializer = CustomerTypeChartSerializer(type_data, many=True)
        return Response(serializer.data)