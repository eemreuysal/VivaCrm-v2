from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import os
import json
import logging

from customers.models import Customer
from products.models import Product
from orders.models import Order
from invoices.models import Invoice

User = get_user_model()
logger = logging.getLogger(__name__)

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admin users can access admin panel views"""
    def test_func(self):
        return self.request.user.is_staff


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin panel main dashboard"""
    template_name = "admin_panel/dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # System statistics
        context["total_users"] = User.objects.count()
        context["active_users"] = User.objects.filter(is_active=True).count()
        context["total_customers"] = Customer.objects.count()
        context["total_products"] = Product.objects.count()
        context["total_orders"] = Order.objects.count()
        context["total_invoices"] = Invoice.objects.count()
        
        # Recent users
        context["recent_users"] = User.objects.order_by("-date_joined")[:5]
        
        # Recent activity (placeholder for now)
        context["recent_activity"] = []
        
        return context


class AdminUserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin user management list view"""
    model = User
    template_name = "admin_panel/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        
        if search_query:
            queryset = queryset.filter(
                models.Q(username__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query) |
                models.Q(email__icontains=search_query)
            )
            
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'staff':
            queryset = queryset.filter(is_staff=True)
        
        return queryset.order_by('-date_joined')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['active_count'] = User.objects.filter(is_active=True).count()
        context['inactive_count'] = User.objects.filter(is_active=False).count()
        context['staff_count'] = User.objects.filter(is_staff=True).count()
        return context


class AdminUserDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Admin user detail view"""
    model = User
    template_name = "admin_panel/user_detail.html"
    context_object_name = "user_obj"  # Renamed to avoid conflict with request.user
    slug_field = "username"
    slug_url_kwarg = "username"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get user activity statistics
        if hasattr(user, 'customer_set'):
            context['customers_created'] = user.customer_set.count()
        else:
            context['customers_created'] = 0
            
        if hasattr(user, 'order_set'):
            context['orders_created'] = user.order_set.count()
        else:
            context['orders_created'] = 0
            
        if hasattr(user, 'product_set'):
            context['products_created'] = user.product_set.count()
        else:
            context['products_created'] = 0
            
        # Last login and activity
        context['last_login'] = user.last_login
        
        return context


class SystemSettingsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """System settings view"""
    template_name = "admin_panel/system_settings.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add system settings here
        return context
    
    def post(self, request):
        # Handle system settings update
        setting_name = request.POST.get('setting_name')
        setting_value = request.POST.get('setting_value')
        
        # Logic to update system settings would go here
        
        messages.success(request, _('Sistem ayarları güncellendi.'))
        return redirect('admin_panel:system-settings')


class SystemLogsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """System logs view"""
    template_name = "admin_panel/system_logs.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # This is a placeholder - in a real app, you'd want to integrate with 
        # a proper logging system or read from log files
        context['logs'] = [
            {
                'timestamp': timezone.now(),
                'level': 'INFO',
                'message': 'Bu bir örnek log kaydıdır.',
                'user': self.request.user.username,
            }
        ]
        
        return context


class BackupView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Database backup and restore view"""
    template_name = "admin_panel/backup.html"
    
    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'backup':
            # Implement database backup logic here
            # This is just a placeholder
            messages.success(request, _('Veritabanı yedeklemesi başarıyla oluşturuldu.'))
        elif action == 'restore':
            # Implement database restore logic here
            # This is just a placeholder
            messages.success(request, _('Veritabanı başarıyla geri yüklendi.'))
            
        return redirect('admin_panel:backup')