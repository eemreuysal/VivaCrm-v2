from rest_framework import serializers
from reports.models import SavedReport
from django.contrib.auth import get_user_model

User = get_user_model()


class UserReferenceSerializer(serializers.ModelSerializer):
    """Simple serializer for referencing users."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class SavedReportSerializer(serializers.ModelSerializer):
    """Serializer for saved reports."""
    owner_details = UserReferenceSerializer(source='owner', read_only=True)
    type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedReport
        fields = [
            'id', 'name', 'type', 'type_display', 'description', 'parameters',
            'owner', 'owner_details', 'is_shared', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_type_display(self, obj):
        return obj.get_type_display()


# Serializers for report data
class SalesSummarySerializer(serializers.Serializer):
    """Serializer for sales summary report."""
    order_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    cancellation_rate = serializers.FloatField()


class SalesByPeriodSerializer(serializers.Serializer):
    """Serializer for sales by period report."""
    period = serializers.DateTimeField()
    order_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=12, decimal_places=2)


class TopProductSerializer(serializers.Serializer):
    """Serializer for top products report."""
    product__id = serializers.IntegerField()
    product__name = serializers.CharField()
    product__code = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class TopCategorySerializer(serializers.Serializer):
    """Serializer for top categories report."""
    product__category__id = serializers.IntegerField()
    product__category__name = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class TopCustomerSerializer(serializers.Serializer):
    """Serializer for top customers report."""
    customer__id = serializers.IntegerField()
    customer__name = serializers.CharField()
    customer__company_name = serializers.CharField(allow_null=True)
    order_count = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)


class InventorySummarySerializer(serializers.Serializer):
    """Serializer for inventory summary."""
    total_products = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=12, decimal_places=2)


class InventoryProductSerializer(serializers.Serializer):
    """Serializer for inventory product details."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()
    stock = serializers.IntegerField()
    low_stock = serializers.BooleanField()
    out_of_stock = serializers.BooleanField()
    category__name = serializers.CharField(allow_null=True)


class InventoryReportSerializer(serializers.Serializer):
    """Serializer for complete inventory report."""
    summary = InventorySummarySerializer()
    products = InventoryProductSerializer(many=True)


class PaymentStatisticsSerializer(serializers.Serializer):
    """Serializer for payment statistics report."""
    payment_method = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage = serializers.FloatField()


class CustomerAcquisitionSerializer(serializers.Serializer):
    """Serializer for customer acquisition report."""
    period = serializers.DateTimeField()
    new_customers = serializers.IntegerField()


# Serializers for report parameters
class SalesReportParamsSerializer(serializers.Serializer):
    """Serializer for sales report parameters."""
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    period = serializers.ChoiceField(choices=['day', 'week', 'month'], default='month', required=False)
    status = serializers.CharField(required=False, allow_null=True)
    limit = serializers.IntegerField(min_value=1, max_value=50, default=10, required=False)


class InventoryReportParamsSerializer(serializers.Serializer):
    """Serializer for inventory report parameters."""
    category = serializers.IntegerField(required=False, allow_null=True)
    low_stock_threshold = serializers.IntegerField(min_value=1, default=10, required=False)


class CustomerReportParamsSerializer(serializers.Serializer):
    """Serializer for customer report parameters."""
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    period = serializers.ChoiceField(choices=['day', 'week', 'month'], default='month', required=False)
    limit = serializers.IntegerField(min_value=1, max_value=50, default=10, required=False)