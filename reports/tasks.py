from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import pandas as pd
import os
from django.db.models import Sum, Count, F, Avg
from .models import SavedReport


@shared_task
def generate_sales_report(start_date=None, end_date=None, report_format='excel'):
    """
    Generate a sales report for the specified date range.
    Report can be saved as Excel or CSV.
    """
    from orders.models import Order, OrderItem
    
    # Define date range if not specified
    if not end_date:
        end_date = timezone.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)  # Default to 30 days
    
    # Convert string dates to date objects if needed
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()
    
    # Query orders in the date range
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Aggregate order data
    order_summary = orders.values('status').annotate(
        count=Count('id'),
        total_revenue=Sum('total_amount')
    )
    
    # Get product sales data
    product_sales = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        order__created_at__date__lte=end_date
    ).values(
        'product__name',
        'product__sku',
        'product__category__name'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('price') * F('quantity')),
        average_price=Avg('price')
    ).order_by('-total_revenue')
    
    # Create dataframes
    orders_df = pd.DataFrame(list(order_summary))
    products_df = pd.DataFrame(list(product_sales))
    
    # Define the output path
    report_name = f"sales_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Save the report based on the requested format
    if report_format.lower() == 'excel':
        file_path = os.path.join(reports_dir, f"{report_name}.xlsx")
        with pd.ExcelWriter(file_path) as writer:
            orders_df.to_excel(writer, sheet_name='Orders Summary', index=False)
            products_df.to_excel(writer, sheet_name='Product Sales', index=False)
    else:  # CSV format
        orders_file = os.path.join(reports_dir, f"{report_name}_orders.csv")
        products_file = os.path.join(reports_dir, f"{report_name}_products.csv")
        orders_df.to_csv(orders_file, index=False)
        products_df.to_csv(products_file, index=False)
        file_path = orders_file  # Return the path to the first file
    
    # Create a saved report record
    SavedReport.objects.create(
        name=f"Sales Report {start_date} to {end_date}",
        report_type='sales',
        file_path=file_path,
        parameters={
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'format': report_format
        }
    )
    
    return file_path


@shared_task
def generate_customer_activity_report(days=90, report_format='excel'):
    """
    Generate a report on customer activity for the past X days.
    """
    from customers.models import Customer
    from orders.models import Order
    from django.db.models import Max, Count
    
    # Define the time period
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Query customers and their activity
    customers = Customer.objects.annotate(
        order_count=Count('orders', filter=F('orders__created_at__date__gte') == start_date),
        last_order_date=Max('orders__created_at'),
        total_spent=Sum('orders__total_amount', filter=F('orders__created_at__date__gte') == start_date)
    ).order_by('-total_spent')
    
    # Create the dataframe
    data = []
    for customer in customers:
        data.append({
            'customer_id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'company': customer.company_name,
            'order_count': customer.order_count,
            'last_order_date': customer.last_order_date,
            'total_spent': customer.total_spent or 0,
            'is_active': customer.is_active
        })
    
    df = pd.DataFrame(data)
    
    # Define the output path
    report_name = f"customer_activity_{days}_days_{end_date.strftime('%Y%m%d')}"
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Save the report based on the requested format
    if report_format.lower() == 'excel':
        file_path = os.path.join(reports_dir, f"{report_name}.xlsx")
        df.to_excel(file_path, index=False)
    else:  # CSV format
        file_path = os.path.join(reports_dir, f"{report_name}.csv")
        df.to_csv(file_path, index=False)
    
    # Create a saved report record
    SavedReport.objects.create(
        name=f"Customer Activity Report ({days} days)",
        report_type='customer_activity',
        file_path=file_path,
        parameters={
            'days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'format': report_format
        }
    )
    
    return file_path


@shared_task
def send_scheduled_reports_to_users():
    """
    Find all saved reports with subscribed users and email the reports to them.
    """
    from accounts.models import User
    
    # Get all staff users
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    
    # Get the most recent saved reports
    recent_reports = SavedReport.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    ).order_by('-created_at')
    
    # Group by report type to get the most recent of each type
    latest_reports = {}
    for report in recent_reports:
        if report.report_type not in latest_reports:
            latest_reports[report.report_type] = report
    
    # Send each report to staff users
    for report_type, report in latest_reports.items():
        # Check if file exists
        if not os.path.exists(report.file_path):
            continue
        
        subject = f"Scheduled Report: {report.name}"
        text_content = f"""
        Dear Staff Member,
        
        Please find attached the latest {report.name}.
        
        This report was generated on {report.created_at.strftime('%Y-%m-%d %H:%M')}.
        
        Best regards,
        VivaCRM System
        """
        
        for user in staff_users:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            # Attach the report file
            with open(report.file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(report.file_path)
                msg.attach(file_name, file_data, 'application/octet-stream')
            
            msg.send()
    
    return f"Sent {len(latest_reports)} reports to {staff_users.count()} staff users"