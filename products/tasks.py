from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F
from .models import Product, StockMovement


@shared_task
def check_low_stock_levels():
    """
    Check for products with stock levels below their thresholds and send notifications.
    """
    # Find products below threshold stock levels
    low_stock_products = Product.objects.filter(
        current_stock__lt=F('threshold_stock'),
        threshold_stock__gt=0  # Only include products that have a threshold set
    ).select_related('category')
    
    # If no products have low stock, return early
    if not low_stock_products.exists():
        return "No products with low stock found"
    
    # Build the email message
    subject = "Low Stock Alert - Action Required"
    message_lines = ["The following products are below their minimum stock levels:", ""]
    
    for product in low_stock_products:
        message_lines.append(
            f"• {product.name} ({product.sku}): "
            f"Current stock: {product.current_stock}, "
            f"Threshold: {product.threshold_stock}, "
            f"Category: {product.category.name}"
        )
    
    message_lines.append("")
    message_lines.append("Please restock these items as soon as possible.")
    message = "\n".join(message_lines)
    
    # Get staff emails to notify
    from accounts.models import User
    staff_emails = User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True)
    
    # Send the email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(staff_emails),
        fail_silently=False,
    )
    
    return f"Sent low stock alerts for {low_stock_products.count()} products"


@shared_task
def generate_stock_movements_report():
    """
    Generate a report of all stock movements for the past month.
    This can be extended to save the report to a file or send it via email.
    """
    from django.utils import timezone
    from datetime import timedelta
    import csv
    import os
    
    # Define the time period (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Query stock movements
    movements = StockMovement.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product')
    
    # Create the reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate CSV file
    filename = f"stock_movements_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Product', 'SKU', 'Type', 'Quantity', 'Reference', 'User'])
        
        for movement in movements:
            writer.writerow([
                movement.created_at.strftime('%Y-%m-%d %H:%M'),
                movement.product.name,
                movement.product.sku,
                movement.get_movement_type_display(),
                movement.quantity,
                movement.reference,
                movement.created_by.get_full_name() if movement.created_by else 'System'
            ])
    
    return f"Stock movements report generated at {filepath}"


@shared_task
def expire_product_promotions():
    """
    Check for products with expired sale prices and reset them to regular prices.
    """
    from django.utils import timezone
    
    # Find products with expired sale_end_date
    expired_products = Product.objects.filter(
        sale_price__isnull=False,
        sale_end_date__lt=timezone.now()
    )
    
    count = 0
    for product in expired_products:
        product.sale_price = None
        product.sale_end_date = None
        product.save(update_fields=['sale_price', 'sale_end_date'])
        count += 1
    
    return f"Reset pricing for {count} products with expired promotions"