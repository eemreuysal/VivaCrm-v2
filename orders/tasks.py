from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import F, Sum

from .models import Order, OrderItem


@shared_task
def send_order_reminder(days=3):
    """
    Send reminder emails for orders that are still in 'pending' or 'processing' state
    after a specified number of days.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    pending_orders = Order.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['pending', 'processing']
    ).select_related('customer')
    
    count = 0
    for order in pending_orders:
        context = {
            'order': order,
            'customer_name': order.customer.name,
            'order_date': order.created_at.strftime('%d/%m/%Y'),
            'order_number': order.order_number,
            'status': order.get_status_display(),
        }
        
        html_message = render_to_string('emails/orders/order_reminder.html', context)
        text_message = render_to_string('emails/orders/order_reminder.txt', context)
        
        send_mail(
            subject=f"Reminder: Order #{order.order_number} is still {order.get_status_display()}",
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            fail_silently=False,
        )
        count += 1
    
    return f"Sent {count} order reminder emails"


@shared_task
def update_product_sales_stats():
    """
    Update the sales statistics for each product based on order data.
    This can be used for reporting and analytics.
    """
    from products.models import Product
    
    # Get completed orders
    completed_orders = OrderItem.objects.filter(
        order__status='completed'
    ).values('product').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('price') * F('quantity'))
    )
    
    # Update product statistics
    for item in completed_orders:
        try:
            product = Product.objects.get(id=item['product'])
            product.total_sales = item['total_quantity']
            product.total_revenue = item['total_revenue']
            product.save(update_fields=['total_sales', 'total_revenue'])
        except Product.DoesNotExist:
            continue
    
    return "Product sales statistics updated successfully"


@shared_task
def cancel_abandoned_orders(days=7):
    """
    Cancel orders that have been in 'pending' status for too long.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    abandoned_orders = Order.objects.filter(
        created_at__lt=cutoff_date,
        status='pending'
    )
    
    count = 0
    for order in abandoned_orders:
        order.status = 'cancelled'
        order.notes = f"{order.notes}\nAutomatically cancelled due to inactivity after {days} days."
        order.save()
        count += 1
    
    return f"Cancelled {count} abandoned orders"