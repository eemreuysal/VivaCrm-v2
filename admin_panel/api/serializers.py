from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from customers.models import Customer
from products.models import Product
from orders.models import Order, OrderItem
from invoices.models import Invoice

User = get_user_model()


class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard summary data."""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    staff_users = serializers.IntegerField()
    superusers = serializers.IntegerField()
    
    total_customers = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_invoices = serializers.IntegerField()
    
    # Financial metrics
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    weekly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    daily_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Growth metrics
    user_growth = serializers.FloatField()
    customer_growth = serializers.FloatField()
    order_growth = serializers.FloatField()
    revenue_growth = serializers.FloatField()


class SystemStatusSerializer(serializers.Serializer):
    """Serializer for system status information."""
    status = serializers.CharField()
    uptime = serializers.CharField()
    server_time = serializers.DateTimeField()
    database_size = serializers.CharField()
    media_storage_size = serializers.CharField()
    disk_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    cpu_usage = serializers.FloatField()
    is_debug = serializers.BooleanField()
    cache_status = serializers.CharField()
    python_version = serializers.CharField()
    django_version = serializers.CharField()


class LogEntrySerializer(serializers.Serializer):
    """Serializer for system log entries."""
    timestamp = serializers.DateTimeField()
    level = serializers.CharField()
    message = serializers.CharField()
    user = serializers.CharField(allow_null=True)
    path = serializers.CharField(allow_null=True)
    ip_address = serializers.CharField(allow_null=True)
    module = serializers.CharField(allow_null=True)


class BackupSerializer(serializers.Serializer):
    """Serializer for system backups."""
    id = serializers.IntegerField()
    filename = serializers.CharField()
    timestamp = serializers.DateTimeField()
    size = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    can_restore = serializers.BooleanField()


class BackupRequestSerializer(serializers.Serializer):
    """Serializer for backup requests."""
    name = serializers.CharField(required=False, allow_blank=True)
    include_media = serializers.BooleanField(default=False)
    include_uploads = serializers.BooleanField(default=False)


class RestoreRequestSerializer(serializers.Serializer):
    """Serializer for restore requests."""
    backup_id = serializers.IntegerField()
    confirm = serializers.BooleanField(default=False)


class SystemSettingSerializer(serializers.Serializer):
    """Serializer for system settings."""
    key = serializers.CharField()
    value = serializers.JSONField()
    description = serializers.CharField()
    category = serializers.CharField()
    is_public = serializers.BooleanField()


class UserActivitySerializer(serializers.Serializer):
    """Serializer for user activity logs."""
    user = serializers.CharField()
    action = serializers.CharField()
    timestamp = serializers.DateTimeField()
    details = serializers.JSONField(allow_null=True)
    ip_address = serializers.CharField(allow_null=True)
    user_agent = serializers.CharField(allow_null=True)