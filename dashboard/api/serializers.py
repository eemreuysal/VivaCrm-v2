from rest_framework import serializers
from customers.models import Customer
from products.models import Product
from orders.models import Order, OrderItem


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary data."""
    total_customers = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_orders = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    last_30d_orders_count = serializers.IntegerField()


class RecentOrderSerializer(serializers.ModelSerializer):
    """Serializer for recent orders on dashboard."""
    customer_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display')
    status_badge = serializers.CharField(source='get_status_badge')
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'created_at', 'total_amount',
            'status', 'status_display', 'status_badge'
        ]
    
    def get_customer_name(self, obj):
        return obj.customer.name


class TopCustomerSerializer(serializers.ModelSerializer):
    """Serializer for top customers on dashboard."""
    order_count = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'company_name', 'type', 'email', 
            'order_count', 'total_spent'
        ]


class TopProductSerializer(serializers.Serializer):
    """Serializer for top products on dashboard."""
    product__id = serializers.IntegerField()
    product__name = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class LowStockProductSerializer(serializers.ModelSerializer):
    """Serializer for low stock products on dashboard."""
    
    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'stock', 'threshold_stock'
        ]


class SalesChartDataSerializer(serializers.Serializer):
    """Serializer for sales chart data."""
    date = serializers.DateField()
    orders = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class ProductCategoryChartSerializer(serializers.Serializer):
    """Serializer for product category distribution chart."""
    category = serializers.CharField()
    product_count = serializers.IntegerField()


class OrderStatusChartSerializer(serializers.Serializer):
    """Serializer for order status distribution chart."""
    status = serializers.CharField()
    status_display = serializers.CharField()
    order_count = serializers.IntegerField()


class CustomerTypeChartSerializer(serializers.Serializer):
    """Serializer for customer type distribution chart."""
    type = serializers.CharField()
    type_display = serializers.CharField()
    customer_count = serializers.IntegerField()