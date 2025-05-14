from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime
import os
import sys
import time
import platform
import psutil
import django
import logging

from customers.models import Customer
from products.models import Product
from orders.models import Order
from invoices.models import Invoice
from django.contrib.auth import get_user_model

from .serializers import (
    AdminDashboardSerializer, SystemStatusSerializer, LogEntrySerializer,
    BackupSerializer, BackupRequestSerializer, RestoreRequestSerializer,
    SystemSettingSerializer, UserActivitySerializer
)

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow superusers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def admin_dashboard(request):
    """
    API endpoint for admin dashboard summary data.
    """
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_prev_month = (start_of_month - timedelta(days=1)).replace(day=1)
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Entity counts
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_invoices = Invoice.objects.count()
    
    # Revenue statistics
    total_revenue = Order.objects.filter(
        status__in=['completed', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        status__in=['completed', 'delivered'],
        order_date__gte=start_of_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    weekly_revenue = Order.objects.filter(
        status__in=['completed', 'delivered'],
        order_date__gte=start_of_week
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    daily_revenue = Order.objects.filter(
        status__in=['completed', 'delivered'],
        order_date__gte=start_of_day
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Growth metrics
    prev_month_users = User.objects.filter(
        date_joined__lt=start_of_month
    ).count()
    user_growth = ((total_users - prev_month_users) / prev_month_users * 100) if prev_month_users > 0 else 0
    
    prev_month_customers = Customer.objects.filter(
        created_at__lt=start_of_month
    ).count()
    customer_growth = ((total_customers - prev_month_customers) / prev_month_customers * 100) if prev_month_customers > 0 else 0
    
    prev_month_orders = Order.objects.filter(
        created_at__lt=start_of_month
    ).count()
    order_growth = ((total_orders - prev_month_orders) / prev_month_orders * 100) if prev_month_orders > 0 else 0
    
    prev_month_revenue = Order.objects.filter(
        status__in=['completed', 'delivered'],
        order_date__gte=start_of_prev_month,
        order_date__lt=start_of_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    revenue_growth = ((monthly_revenue - prev_month_revenue) / prev_month_revenue * 100) if prev_month_revenue > 0 else 0
    
    # Prepare data
    data = {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'total_customers': total_customers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_invoices': total_invoices,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'weekly_revenue': weekly_revenue,
        'daily_revenue': daily_revenue,
        'user_growth': user_growth,
        'customer_growth': customer_growth,
        'order_growth': order_growth,
        'revenue_growth': revenue_growth
    }
    
    serializer = AdminDashboardSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def system_status(request):
    """
    API endpoint for system status.
    """
    # Get system info
    uptime = int(time.time() - psutil.boot_time())
    uptime_str = f"{uptime // 86400}d {(uptime % 86400) // 3600}h {(uptime % 3600) // 60}m"
    
    # Database size (example implementation - would need to be modified based on DB backend)
    try:
        # This is just a placeholder - in a real app, you'd need database-specific code
        database_size = "Unknown"  
    except:
        database_size = "Unknown"
    
    # Media storage size
    media_path = os.path.join(settings.BASE_DIR, 'media')
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(media_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        media_storage_size = f"{total_size / (1024 * 1024):.2f} MB"
    except:
        media_storage_size = "Unknown"
    
    # System resources
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    cpu_usage = psutil.cpu_percent(interval=0.5)
    
    # Prepare data
    data = {
        'status': 'healthy',  # Default status - could be changed based on checks
        'uptime': uptime_str,
        'server_time': timezone.now(),
        'database_size': database_size,
        'media_storage_size': media_storage_size,
        'disk_usage': disk_usage,
        'memory_usage': memory_usage,
        'cpu_usage': cpu_usage,
        'is_debug': settings.DEBUG,
        'cache_status': 'operational',  # Placeholder - would need actual cache check
        'python_version': platform.python_version(),
        'django_version': django.get_version()
    }
    
    serializer = SystemStatusSerializer(data)
    return Response(serializer.data)


class SystemLogsView(APIView):
    """
    API endpoint for system logs.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # This is a placeholder - in a real app, you'd need to implement
        # actual log parsing from files or database
        
        # Example log entries
        logs = [
            {
                'timestamp': timezone.now(),
                'level': 'INFO',
                'message': 'Example log message',
                'user': request.user.username,
                'path': '/api/admin/logs/',
                'ip_address': request.META.get('REMOTE_ADDR'),
                'module': 'admin_panel.api.views'
            }
        ]
        
        # Filter logs by level if specified
        level = request.query_params.get('level')
        if level:
            logs = [log for log in logs if log['level'] == level.upper()]
        
        # Filter logs by user if specified
        user = request.query_params.get('user')
        if user:
            logs = [log for log in logs if log.get('user') == user]
        
        # Filter logs by date range if specified
        start_date = request.query_params.get('start_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            logs = [log for log in logs if log['timestamp'] >= start_date]
            
        end_date = request.query_params.get('end_date')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            logs = [log for log in logs if log['timestamp'] <= end_date]
        
        # Search in log messages
        search = request.query_params.get('search')
        if search:
            logs = [log for log in logs if search.lower() in log['message'].lower()]
        
        serializer = LogEntrySerializer(logs, many=True)
        return Response(serializer.data)


class BackupView(APIView):
    """
    API endpoint for system backups.
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]
    
    def get(self, request):
        # This is a placeholder - in a real app, you'd need to implement
        # actual backup list retrieval
        
        # Example backups
        backups = [
            {
                'id': 1,
                'filename': 'backup_20250514_143000.zip',
                'timestamp': timezone.now(),
                'size': '10.5 MB',
                'type': 'Full Backup',
                'status': 'Completed',
                'can_restore': True
            }
        ]
        
        serializer = BackupSerializer(backups, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        # Validate request
        serializer = BackupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract parameters
        name = serializer.validated_data.get('name', '')
        include_media = serializer.validated_data.get('include_media', False)
        include_uploads = serializer.validated_data.get('include_uploads', False)
        
        # This is a placeholder - in a real app, you'd implement actual backup creation
        # Return mock response
        return Response({
            'status': 'success',
            'message': 'Backup started',
            'backup_id': 2
        })


class RestoreView(APIView):
    """
    API endpoint for restoring from backup.
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]
    
    def post(self, request):
        # Validate request
        serializer = RestoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract parameters
        backup_id = serializer.validated_data.get('backup_id')
        confirm = serializer.validated_data.get('confirm', False)
        
        if not confirm:
            return Response({
                'status': 'error',
                'message': 'Confirmation required to proceed with restore'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # This is a placeholder - in a real app, you'd implement actual restore logic
        # Return mock response
        return Response({
            'status': 'success',
            'message': f'Restore from backup ID {backup_id} started'
        })


class SystemSettingsView(APIView):
    """
    API endpoint for system settings.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # This is a placeholder - in a real app, you'd retrieve actual system settings
        
        # Example settings
        settings_data = [
            {
                'key': 'company_name',
                'value': 'VivaCRM',
                'description': 'Company name displayed throughout the application',
                'category': 'general',
                'is_public': True
            },
            {
                'key': 'email_sender',
                'value': 'info@vivacrm.com',
                'description': 'Default email sender address',
                'category': 'email',
                'is_public': True
            }
        ]
        
        # Filter by category if specified
        category = request.query_params.get('category')
        if category:
            settings_data = [s for s in settings_data if s['category'] == category]
        
        serializer = SystemSettingSerializer(settings_data, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        # Validate request
        serializer = SystemSettingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # This is a placeholder - in a real app, you'd update the actual setting
        return Response({
            'status': 'success',
            'message': 'Setting updated successfully'
        })


class UserActivityView(APIView):
    """
    API endpoint for user activity logs.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # This is a placeholder - in a real app, you'd retrieve actual user activity logs
        
        # Example activities
        activities = [
            {
                'user': request.user.username,
                'action': 'login',
                'timestamp': timezone.now() - timedelta(hours=1),
                'details': None,
                'ip_address': '127.0.0.1',
                'user_agent': 'Mozilla/5.0'
            }
        ]
        
        # Filter by user if specified
        user = request.query_params.get('user')
        if user:
            activities = [a for a in activities if a['user'] == user]
        
        # Filter by action if specified
        action = request.query_params.get('action')
        if action:
            activities = [a for a in activities if a['action'] == action]
        
        # Filter by date range if specified
        start_date = request.query_params.get('start_date')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            activities = [a for a in activities if a['timestamp'] >= start_date]
            
        end_date = request.query_params.get('end_date')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            activities = [a for a in activities if a['timestamp'] <= end_date]
        
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)