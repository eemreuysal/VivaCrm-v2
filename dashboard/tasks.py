from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import json
import os
from django.conf import settings
from django.db.models import Count, Sum, Avg, F


@shared_task
def generate_dashboard_cache_data():
    """
    Generate and cache data for the dashboard to improve performance.
    Stores the data as JSON files in a cache directory.
    """
    from orders.models import Order
    from products.models import Product
    from customers.models import Customer
    from invoices.models import Invoice
    
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(settings.MEDIA_ROOT, 'cache', 'dashboard')
    os.makedirs(cache_dir, exist_ok=True)
    
    # Time ranges
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    # ------------------- Sales Summary -------------------
    
    # Today's sales
    today_sales = Order.objects.filter(created_at__date=today).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Yesterday's sales
    yesterday_sales = Order.objects.filter(created_at__date=yesterday).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # This week's sales
    this_week_sales = Order.objects.filter(
        created_at__date__gte=this_week_start,
        created_at__date__lte=today
    ).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Last week's sales
    last_week_sales = Order.objects.filter(
        created_at__date__gte=last_week_start,
        created_at__date__lt=this_week_start
    ).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # This month's sales
    this_month_sales = Order.objects.filter(
        created_at__date__gte=this_month_start,
        created_at__date__lte=today
    ).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Last month's sales
    last_month_sales = Order.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lt=this_month_start
    ).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Calculate changes
    sales_data = {
        'today': {
            'count': today_sales['count'] or 0,
            'total': float(today_sales['total'] or 0),
            'change': (
                ((today_sales['total'] or 0) - (yesterday_sales['total'] or 0)) / 
                (yesterday_sales['total'] or 1) * 100
            ) if yesterday_sales['total'] else 0
        },
        'this_week': {
            'count': this_week_sales['count'] or 0,
            'total': float(this_week_sales['total'] or 0),
            'change': (
                ((this_week_sales['total'] or 0) - (last_week_sales['total'] or 0)) / 
                (last_week_sales['total'] or 1) * 100
            ) if last_week_sales['total'] else 0
        },
        'this_month': {
            'count': this_month_sales['count'] or 0,
            'total': float(this_month_sales['total'] or 0),
            'change': (
                ((this_month_sales['total'] or 0) - (last_month_sales['total'] or 0)) / 
                (last_month_sales['total'] or 1) * 100
            ) if last_month_sales['total'] else 0
        }
    }
    
    # Save sales data to cache
    with open(os.path.join(cache_dir, 'sales_summary.json'), 'w') as f:
        json.dump(sales_data, f)
    
    # ------------------- Product Statistics -------------------
    
    # Top selling products this month
    top_products = Product.objects.filter(
        orderitem__order__created_at__date__gte=this_month_start
    ).annotate(
        units_sold=Sum('orderitem__quantity'),
        revenue=Sum(F('orderitem__price') * F('orderitem__quantity'))
    ).order_by('-units_sold')[:10].values('id', 'name', 'sku', 'units_sold', 'revenue')
    
    # Low stock products
    low_stock = Product.objects.filter(
        current_stock__lt=F('threshold_stock'),
        threshold_stock__gt=0
    ).values('id', 'name', 'sku', 'current_stock', 'threshold_stock')
    
    # Save product data to cache
    product_data = {
        'top_products': list(top_products),
        'low_stock': list(low_stock)
    }
    with open(os.path.join(cache_dir, 'product_stats.json'), 'w') as f:
        json.dump(product_data, f, default=str)
    
    # ------------------- Customer Statistics -------------------
    
    # New customers this month
    new_customers = Customer.objects.filter(
        created_at__date__gte=this_month_start
    ).count()
    
    # Top customers this month by order value
    top_customers = Customer.objects.filter(
        orders__created_at__date__gte=this_month_start
    ).annotate(
        total_spent=Sum('orders__total_amount'),
        order_count=Count('orders')
    ).order_by('-total_spent')[:10].values(
        'id', 'name', 'email', 'company_name', 'total_spent', 'order_count'
    )
    
    # Save customer data to cache
    customer_data = {
        'new_customers': new_customers,
        'top_customers': list(top_customers)
    }
    with open(os.path.join(cache_dir, 'customer_stats.json'), 'w') as f:
        json.dump(customer_data, f, default=str)
    
    # ------------------- Invoice Statistics -------------------
    
    # Unpaid invoices
    unpaid_invoices = Invoice.objects.filter(
        is_paid=False
    ).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Overdue invoices
    overdue_invoices = Invoice.objects.filter(
        is_paid=False,
        due_date__lt=today
    ).aggregate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Save invoice data to cache
    invoice_data = {
        'unpaid': {
            'count': unpaid_invoices['count'] or 0,
            'total': float(unpaid_invoices['total'] or 0)
        },
        'overdue': {
            'count': overdue_invoices['count'] or 0,
            'total': float(overdue_invoices['total'] or 0)
        }
    }
    with open(os.path.join(cache_dir, 'invoice_stats.json'), 'w') as f:
        json.dump(invoice_data, f)
    
    return "Dashboard cache data has been generated successfully"


@shared_task
def daily_system_status_report():
    """
    Generate a daily report of system status including database size,
    number of records in each model, etc.
    """
    from django.db import connection
    from accounts.models import User
    from customers.models import Customer
    from products.models import Product, Category
    from orders.models import Order
    from invoices.models import Invoice
    
    # Get record counts
    stats = {
        'users': User.objects.count(),
        'customers': Customer.objects.count(),
        'products': Product.objects.count(),
        'categories': Category.objects.count(),
        'orders': Order.objects.count(),
        'invoices': Invoice.objects.count(),
    }
    
    # Get database size for SQLite (this will be different for PostgreSQL)
    db_size = os.path.getsize(settings.DATABASES['default']['NAME'])
    stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
    
    # Get table sizes
    tables = [
        'accounts_user',
        'customers_customer',
        'products_product',
        'products_category',
        'orders_order',
        'orders_orderitem',
        'invoices_invoice',
        'invoices_invoiceitem'
    ]
    
    table_sizes = {}
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_sizes[table] = count
    
    stats['table_sizes'] = table_sizes
    
    # Save to file
    report_date = timezone.now().strftime('%Y-%m-%d')
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'system')
    os.makedirs(reports_dir, exist_ok=True)
    
    file_path = os.path.join(reports_dir, f"system_stats_{report_date}.json")
    with open(file_path, 'w') as f:
        json.dump(stats, f, indent=4)
    
    return f"System status report generated at {file_path}"