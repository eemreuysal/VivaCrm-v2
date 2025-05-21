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
        from .models import SystemSettings
        
        context = super().get_context_data(**kwargs)
        
        # Get settings from database, grouped by category
        settings_by_category = {}
        for category, _ in SystemSettings.CATEGORY_CHOICES:
            settings_by_category[category] = SystemSettings.objects.filter(category=category)
        
        context['settings_by_category'] = settings_by_category
        
        # Add specific settings for the form defaults
        context['company_name'] = SystemSettings.get_setting('company_name', 'VivaCRM')
        context['company_short_name'] = SystemSettings.get_setting('company_short_name', 'Viva')
        context['company_email'] = SystemSettings.get_setting('company_email', 'info@vivacrm.com')
        context['company_phone'] = SystemSettings.get_setting('company_phone', '+90 212 123 4567')
        context['company_website'] = SystemSettings.get_setting('company_website', 'https://vivacrm.com')
        context['company_address'] = SystemSettings.get_setting('company_address', 'İstanbul, Türkiye')
        
        # Email settings
        context['smtp_host'] = SystemSettings.get_setting('smtp_host', 'smtp.example.com')
        context['smtp_port'] = SystemSettings.get_setting('smtp_port', '587')
        context['smtp_username'] = SystemSettings.get_setting('smtp_username', 'user@example.com')
        context['smtp_password'] = SystemSettings.get_setting('smtp_password', 'password')
        context['smtp_use_tls'] = SystemSettings.get_setting('smtp_use_tls', 'True') == 'True'
        context['default_from_email'] = SystemSettings.get_setting('default_from_email', 'info@vivacrm.com')
        
        # Advanced settings
        context['items_per_page'] = SystemSettings.get_setting('items_per_page', '25')
        context['default_currency'] = SystemSettings.get_setting('default_currency', 'USD')
        context['date_format'] = SystemSettings.get_setting('date_format', 'd.m.Y')
        context['time_format'] = SystemSettings.get_setting('time_format', 'H:i')
        context['enable_debug'] = SystemSettings.get_setting('enable_debug', 'True') == 'True'
        context['enable_maintenance'] = SystemSettings.get_setting('enable_maintenance', 'False') == 'True'
        context['enable_registration'] = SystemSettings.get_setting('enable_registration', 'True') == 'True'
        context['enable_api'] = SystemSettings.get_setting('enable_api', 'True') == 'True'
        
        return context
    
    def post(self, request):
        from .models import SystemSettings
        
        # Handle system settings update
        setting_group = request.POST.get('setting_group')
        
        if setting_group == 'general':
            # General settings
            SystemSettings.set_setting('company_name', request.POST.get('company_name', ''), 
                                      category='general', description='Company name')
            SystemSettings.set_setting('company_short_name', request.POST.get('company_short_name', ''), 
                                      category='general', description='Company short name')
            SystemSettings.set_setting('company_email', request.POST.get('company_email', ''), 
                                      category='general', description='Company email')
            SystemSettings.set_setting('company_phone', request.POST.get('company_phone', ''), 
                                      category='general', description='Company phone')
            SystemSettings.set_setting('company_website', request.POST.get('company_website', ''), 
                                      category='general', description='Company website')
            SystemSettings.set_setting('company_address', request.POST.get('company_address', ''), 
                                      category='general', description='Company address')
            
        elif setting_group == 'email':
            # Email settings
            SystemSettings.set_setting('smtp_host', request.POST.get('smtp_host', ''), 
                                      category='email', description='SMTP Host')
            SystemSettings.set_setting('smtp_port', request.POST.get('smtp_port', ''), 
                                      category='email', description='SMTP Port')
            SystemSettings.set_setting('smtp_username', request.POST.get('smtp_username', ''), 
                                      category='email', description='SMTP Username')
            SystemSettings.set_setting('smtp_password', request.POST.get('smtp_password', ''), 
                                      category='email', description='SMTP Password', is_public=False)
            SystemSettings.set_setting('smtp_use_tls', 'True' if 'smtp_use_tls' in request.POST else 'False', 
                                      category='email', description='SMTP Use TLS')
            SystemSettings.set_setting('default_from_email', request.POST.get('default_from_email', ''), 
                                      category='email', description='Default From Email')
            
        elif setting_group == 'advanced':
            # Advanced settings
            SystemSettings.set_setting('items_per_page', request.POST.get('items_per_page', '25'), 
                                      category='advanced', description='Items per page')
            SystemSettings.set_setting('default_currency', request.POST.get('default_currency', 'USD'), 
                                      category='advanced', description='Default Currency')
            SystemSettings.set_setting('date_format', request.POST.get('date_format', 'd.m.Y'), 
                                      category='advanced', description='Date Format')
            SystemSettings.set_setting('time_format', request.POST.get('time_format', 'H:i'), 
                                      category='advanced', description='Time Format')
            SystemSettings.set_setting('enable_debug', 'True' if 'enable_debug' in request.POST else 'False', 
                                      category='advanced', description='Enable Debug Mode')
            SystemSettings.set_setting('enable_maintenance', 'True' if 'enable_maintenance' in request.POST else 'False', 
                                      category='advanced', description='Enable Maintenance Mode')
            SystemSettings.set_setting('enable_registration', 'True' if 'enable_registration' in request.POST else 'False', 
                                      category='advanced', description='Enable User Registration')
            SystemSettings.set_setting('enable_api', 'True' if 'enable_api' in request.POST else 'False', 
                                      category='advanced', description='Enable API')
        
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
        from django.contrib.auth import authenticate
        from django.conf import settings
        from django.db import connection
        import subprocess
        import os
        from datetime import datetime
        from .models import SystemSettings
        
        action = request.POST.get('action')
        
        if action == 'backup':
            # Implement database backup logic here
            try:
                backup_name = request.POST.get('backup_name', '')
                include_media = 'include_media' in request.POST
                
                if not backup_name:
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Create backup directory if it doesn't exist
                backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Determine database type and create backup
                db_settings = settings.DATABASES['default']
                db_type = db_settings['ENGINE'].split('.')[-1]
                
                if db_type == 'sqlite3':
                    # SQLite backup
                    db_path = db_settings['NAME']
                    backup_path = os.path.join(backup_dir, f"{backup_name}.sqlite3")
                    
                    # Use Python's file operations for SQLite
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    
                    # Add media files if requested
                    if include_media:
                        media_path = os.path.join(settings.MEDIA_ROOT)
                        media_backup_path = os.path.join(backup_dir, f"{backup_name}_media")
                        
                        # Use system command to copy directory
                        os.makedirs(media_backup_path, exist_ok=True)
                        subprocess.run(['cp', '-r', media_path, media_backup_path])
                
                elif db_type == 'postgresql':
                    # PostgreSQL backup
                    db_name = db_settings['NAME']
                    db_user = db_settings['USER']
                    db_password = db_settings['PASSWORD']
                    db_host = db_settings['HOST'] or 'localhost'
                    
                    backup_path = os.path.join(backup_dir, f"{backup_name}.sql")
                    
                    # Use pg_dump
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db_password
                    subprocess.run([
                        'pg_dump',
                        '-h', db_host,
                        '-U', db_user,
                        '-d', db_name,
                        '-f', backup_path
                    ], env=env)
                    
                    # Add media files if requested
                    if include_media:
                        media_path = os.path.join(settings.MEDIA_ROOT)
                        media_backup_path = os.path.join(backup_dir, f"{backup_name}_media")
                        
                        os.makedirs(media_backup_path, exist_ok=True)
                        subprocess.run(['cp', '-r', media_path, media_backup_path])
                else:
                    # For other databases, show a warning
                    messages.warning(request, _('Otomatik yedekleme sadece SQLite ve PostgreSQL için desteklenmektedir.'))
                    return redirect('admin_panel:backup')
                
                messages.success(request, _(f'Veritabanı yedeklemesi başarıyla oluşturuldu: {backup_name}'))
                
            except Exception as e:
                messages.error(request, _(f'Yedekleme sırasında hata oluştu: {str(e)}'))
                
        elif action == 'restore':
            # Implement database restore logic here
            try:
                if 'backup_file' not in request.FILES:
                    messages.error(request, _('Lütfen bir yedek dosyası seçin.'))
                    return redirect('admin_panel:backup')
                
                # Check confirmation
                if 'confirm_restore' not in request.POST:
                    messages.error(request, _('Geri yükleme işlemi için onay gerekiyor.'))
                    return redirect('admin_panel:backup')
                
                backup_file = request.FILES['backup_file']
                file_name = backup_file.name
                
                # Create temporary directory for restore
                restore_dir = os.path.join(settings.BASE_DIR, 'restore_temp')
                os.makedirs(restore_dir, exist_ok=True)
                
                # Save uploaded file
                file_path = os.path.join(restore_dir, file_name)
                with open(file_path, 'wb+') as destination:
                    for chunk in backup_file.chunks():
                        destination.write(chunk)
                
                # Determine database type and restore
                db_settings = settings.DATABASES['default']
                db_type = db_settings['ENGINE'].split('.')[-1]
                
                if db_type == 'sqlite3':
                    # SQLite restore
                    db_path = db_settings['NAME']
                    
                    # Close all connections first
                    connection.close()
                    
                    # Replace the database file
                    import shutil
                    shutil.copy2(file_path, db_path)
                    
                elif db_type == 'postgresql':
                    # PostgreSQL restore
                    db_name = db_settings['NAME']
                    db_user = db_settings['USER']
                    db_password = db_settings['PASSWORD']
                    db_host = db_settings['HOST'] or 'localhost'
                    
                    # Close all connections first
                    connection.close()
                    
                    # Use psql to restore
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db_password
                    
                    # Drop and recreate the database
                    # WARNING: This is destructive but necessary for a clean restore
                    subprocess.run([
                        'psql',
                        '-h', db_host,
                        '-U', db_user,
                        '-c', f"DROP DATABASE IF EXISTS {db_name};"
                    ], env=env)
                    
                    subprocess.run([
                        'psql',
                        '-h', db_host,
                        '-U', db_user,
                        '-c', f"CREATE DATABASE {db_name};"
                    ], env=env)
                    
                    # Restore from backup
                    subprocess.run([
                        'psql',
                        '-h', db_host,
                        '-U', db_user,
                        '-d', db_name,
                        '-f', file_path
                    ], env=env)
                     
                else:
                    # For other databases, show a warning
                    messages.warning(request, _('Otomatik geri yükleme sadece SQLite ve PostgreSQL için desteklenmektedir.'))
                    return redirect('admin_panel:backup')
                
                messages.success(request, _('Veritabanı başarıyla geri yüklendi.'))
                
                # Clean up temporary files
                os.remove(file_path)
                
            except Exception as e:
                messages.error(request, _(f'Geri yükleme sırasında hata oluştu: {str(e)}'))
                
        elif action == 'reset_db':
            # Implement database reset logic - resets all application data including customers
            # while preserving authentication, user accounts, and system settings
            try:
                # Validate confirmation text
                confirmation_text = request.POST.get('confirmation_text', '')
                if confirmation_text != 'RESET DATABASE':
                    messages.error(request, _('Doğrulama metni yanlış. Sıfırlama işlemi iptal edildi.'))
                    return redirect('admin_panel:backup')
                
                # Check admin password
                admin_password = request.POST.get('admin_password', '')
                if not authenticate(username=request.user.username, password=admin_password):
                    messages.error(request, _('Yönetici şifresi yanlış. Sıfırlama işlemi iptal edildi.'))
                    return redirect('admin_panel:backup')
                
                # Determine database type
                db_settings = settings.DATABASES['default']
                db_type = db_settings['ENGINE'].split('.')[-1]
                
                # Flags for what to keep
                keep_settings = 'keep_settings' in request.POST
                keep_users = 'keep_users' in request.POST
                
                # Store settings if needed
                settings_data = {}
                user_data = {}
                
                if keep_settings:
                    # Export all settings
                    from .models import SystemSettings
                    settings_records = SystemSettings.objects.all()
                    for record in settings_records:
                        settings_data[record.key] = {
                            'value': record.value,
                            'description': record.description,
                            'category': record.category,
                            'is_public': record.is_public
                        }
                
                if keep_users:
                    # Export user data - only admin users
                    User = get_user_model()
                    admin_users = User.objects.filter(is_staff=True)
                    for user in admin_users:
                        user_data[user.username] = {
                            'email': user.email,
                            'password': user.password,  # Hashed password
                            'is_staff': user.is_staff,
                            'is_active': user.is_active,
                            'is_superuser': user.is_superuser,
                            'date_joined': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
                        }
                
                # Always backup users and ensure users are preserved
                keep_users = True  # Force this to be true regardless of checkbox setting
                
                # Get all users first regardless of the database type
                User = get_user_model()
                all_users = User.objects.all()
                user_data = {}
                for user in all_users:
                    user_data[user.username] = {
                        'email': user.email,
                        'password': user.password,  # Hashed password
                        'is_staff': user.is_staff,
                        'is_active': user.is_active,
                        'is_superuser': user.is_superuser,
                        'date_joined': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
                        'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
                    }
                
                # Perform database reset based on type
                if db_type == 'sqlite3':
                    # SQLite reset
                    logger.info("Starting SQLite database reset")
                    
                    # Create a backup before reset
                    db_path = db_settings['NAME']
                    backup_path = f"{db_path}.bak-{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    logger.info(f"Created backup at: {backup_path}")
                    
                    # We'll use a different approach than flush to preserve users
                    # First get the list of tables that are not auth-related
                    cursor = connection.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                    tables = [row[0] for row in cursor.fetchall()]
                    logger.info(f"Found {len(tables)} tables in database")
                    
                    # Filter out auth-related tables but include customer tables
                    tables_to_clear = [
                        t for t in tables 
                        if not (t.startswith('auth_') or t.startswith('django_') or 
                              t == 'accounts_user' or t == 'accounts_userprofile' or
                              t == 'admin_panel_systemsettings')
                    ]
                    
                    # Make sure customer tables are included (forcing these to be cleared)
                    customer_tables = [
                        'customers_customer', 'customers_address', 'customers_contact',
                        'products_product', 'products_category', 'products_productfamily', 
                        'products_productimage', 'products_stockmovement',
                        'orders_order', 'orders_orderitem', 'orders_orderstatus',
                        'invoices_invoice', 'invoices_invoiceitem',
                        'reports_report', 'reports_savedreport'
                    ]
                    
                    # Ensure these tables exist in our list
                    for table in customer_tables:
                        if table in tables and table not in tables_to_clear:
                            tables_to_clear.append(table)
                    
                    # Log the tables we're going to clear
                    logger.info(f"Tables to clear ({len(tables_to_clear)}): {tables_to_clear}")
                    
                    # Force customers_customer to be in the list
                    if 'customers_customer' not in tables_to_clear and 'customers_customer' in tables:
                        tables_to_clear.append('customers_customer')
                        logger.info(f"Forcefully added customers_customer to tables_to_clear")
                    
                    # Disable foreign key constraints for SQLite
                    cursor.execute('PRAGMA foreign_keys = OFF')
                    connection.commit()
                    logger.info("Disabled foreign key constraints")
                    
                    # Clear each table that's not auth-related
                    cleared_tables = []
                    failed_tables = []
                    
                    for table in tables_to_clear:
                        try:
                            # First check if the table exists and has records
                            count_query = f"SELECT COUNT(*) FROM {table}"
                            cursor.execute(count_query)
                            count = cursor.fetchone()[0]
                            logger.info(f"Table {table} has {count} records before deletion")
                            
                            if count > 0:
                                # Then delete the records
                                delete_query = f"DELETE FROM {table};"
                                cursor.execute(delete_query)
                                connection.commit()
                                
                                # Verify the deletion
                                cursor.execute(count_query)
                                new_count = cursor.fetchone()[0]
                                logger.info(f"Table {table} has {new_count} records after deletion")
                                
                                if new_count == 0:
                                    cleared_tables.append(table)
                                    logger.info(f"Successfully cleared table {table}")
                                else:
                                    failed_tables.append(table)
                                    logger.warning(f"Failed to clear all records from {table}. Remaining: {new_count}")
                            else:
                                logger.info(f"Table {table} was already empty")
                                
                        except Exception as e:
                            failed_tables.append(table)
                            logger.error(f"Error clearing table {table}: {str(e)}")
                    
                    # Re-enable foreign key constraints
                    cursor.execute('PRAGMA foreign_keys = ON')
                    connection.commit()
                    logger.info("Re-enabled foreign key constraints")
                    
                    # Log summary
                    logger.info(f"Database reset summary - Cleared: {len(cleared_tables)}, Failed: {len(failed_tables)}")
                    if cleared_tables:
                        logger.info(f"Cleared tables: {cleared_tables}")
                    if failed_tables:
                        logger.error(f"Failed tables: {failed_tables}")
                    
                elif db_type == 'postgresql':
                    # PostgreSQL reset
                    db_name = db_settings['NAME']
                    db_user = db_settings['USER']
                    db_password = db_settings['PASSWORD']
                    db_host = db_settings['HOST'] or 'localhost'
                    
                    # Close all connections first
                    connection.close()
                    
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db_password
                    
                    # Instead of dropping all tables, we'll identify and clear non-auth tables
                    # First, get all tables
                    schema_query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
                    tables_result = subprocess.run([
                        'psql',
                        '-h', db_host,
                        '-U', db_user,
                        '-d', db_name,
                        '-t',  # Tuple-only output
                        '-c', schema_query
                    ], env=env, capture_output=True, text=True)
                    
                    all_tables = tables_result.stdout.strip().split('\n')
                    all_tables = [t.strip() for t in all_tables if t.strip()]
                    
                    # Filter out auth and system-related tables, but include customer tables
                    tables_to_clear = [
                        t for t in all_tables 
                        if not (t.startswith('auth_') or t.startswith('django_') or 
                              t == 'accounts_user' or t == 'accounts_userprofile' or
                              t == 'admin_panel_systemsettings')
                    ]
                    
                    # Make sure customer tables are included (forcing these to be cleared)
                    customer_tables = [
                        'customers_customer', 'customers_address', 'customers_contact',
                        'products_product', 'products_category', 'products_productfamily', 
                        'products_productimage', 'products_stockmovement',
                        'orders_order', 'orders_orderitem', 'orders_orderstatus',
                    ]
                    
                    # Ensure these tables exist in our list
                    for table in customer_tables:
                        if table in all_tables and table not in tables_to_clear:
                            tables_to_clear.append(table)
                    
                    # Log the tables we're going to clear
                    logger.info(f"Tables to clear (PostgreSQL): {tables_to_clear}")
                    
                    # Force customers_customer to be in the list
                    if 'customers_customer' not in tables_to_clear and 'customers_customer' in all_tables:
                        tables_to_clear.append('customers_customer')
                        logger.info(f"Forcefully added customers_customer to tables_to_clear (PostgreSQL)")
                    
                    # Clear content from these tables instead of dropping them
                    for table in tables_to_clear:
                        try:
                            # First check if the table has records
                            count_query = f'SELECT COUNT(*) FROM "{table}";'
                            count_result = subprocess.run([
                                'psql',
                                '-h', db_host,
                                '-U', db_user,
                                '-d', db_name,
                                '-t',  # Tuple-only output
                                '-c', count_query
                            ], env=env, capture_output=True, text=True)
                            count = count_result.stdout.strip()
                            logger.info(f"Table {table} has {count} records before deletion (PostgreSQL)")
                            
                            # Then truncate the table
                            truncate_query = f'TRUNCATE TABLE "{table}" CASCADE;'
                            subprocess.run([
                                'psql',
                                '-h', db_host,
                                '-U', db_user,
                                '-d', db_name,
                                '-c', truncate_query
                            ], env=env)
                            
                            # Log success
                            logger.info(f"Successfully cleared table {table} (PostgreSQL)")
                        except Exception as e:
                            logger.error(f"Error clearing table {table} (PostgreSQL): {str(e)}")
                    
                else:
                    # For other databases, show a warning
                    messages.warning(request, _('Otomatik sıfırlama sadece SQLite ve PostgreSQL için desteklenmektedir.'))
                    return redirect('admin_panel:backup')
                
                # Restore settings if needed
                if keep_settings and settings_data:
                    for key, data in settings_data.items():
                        SystemSettings.set_setting(
                            key=key,
                            value=data['value'],
                            category=data['category'],
                            description=data['description'],
                            is_public=data['is_public']
                        )
                
                # Restore users if needed
                if keep_users and user_data:
                    User = get_user_model()
                    for username, data in user_data.items():
                        try:
                            # Check if the user already exists (might happen if they're created by migrations)
                            if not User.objects.filter(username=username).exists():
                                user = User.objects.create(
                                    username=username,
                                    email=data['email'],
                                    is_staff=data['is_staff'],
                                    is_active=data['is_active'],
                                    is_superuser=data['is_superuser']
                                )
                                # We need to set the password hash directly
                                user.password = data['password']
                                user.save()
                        except Exception as e:
                            logger.error(f"User restoration error for {username}: {str(e)}")
                
                messages.success(request, _('Veritabanı başarıyla sıfırlandı.'))
                
            except Exception as e:
                messages.error(request, _(f'Veritabanı sıfırlama işlemi sırasında hata oluştu: {str(e)}'))
            
        return redirect('admin_panel:backup')