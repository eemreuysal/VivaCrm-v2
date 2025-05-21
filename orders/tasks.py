from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import F, Sum, Q
from django.core.cache import cache
from django.db import transaction
import logging

from .models import Order, OrderItem

logger = logging.getLogger(__name__)


class OptimizedOrderTask:
    """Base class for optimized order tasks with caching."""
    
    @staticmethod
    def cache_key(task_name, *args, **kwargs):
        """Generate a cache key for task results."""
        parts = [f"order_task:{task_name}"]
        parts.extend(str(arg) for arg in args)
        parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return ":".join(parts)
    
    @staticmethod
    def get_cached_result(task_name, *args, **kwargs):
        """Get cached result if available."""
        cache_key = OptimizedOrderTask.cache_key(task_name, *args, **kwargs)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_result(result, task_name, timeout=3600, *args, **kwargs):
        """Cache task result."""
        cache_key = OptimizedOrderTask.cache_key(task_name, *args, **kwargs)
        cache.set(cache_key, result, timeout)
        return result


@shared_task(bind=True, max_retries=3)
def send_order_reminder(self, days=3):
    """
    Optimized order reminder task with batch processing.
    """
    try:
        # Check cache for recent execution
        cache_key = f"order_reminder:{days}:{timezone.now().date()}"
        if cache.get(cache_key):
            logger.info(f"Order reminder for {days} days already sent today")
            return "Reminder already sent today"
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Use select_related and values for better performance
        pending_orders = Order.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['pending', 'processing']
        ).select_related('customer').values(
            'id', 'order_number', 'status', 'created_at',
            'customer__name', 'customer__email'
        )
        
        # Batch process orders
        batch_size = 50
        total_sent = 0
        failed_emails = []
        
        for i in range(0, pending_orders.count(), batch_size):
            batch = list(pending_orders[i:i + batch_size])
            
            for order_data in batch:
                try:
                    context = {
                        'order_number': order_data['order_number'],
                        'customer_name': order_data['customer__name'],
                        'order_date': order_data['created_at'].strftime('%d/%m/%Y'),
                        'status': order_data['status'],
                    }
                    
                    # Check if email template exists, otherwise use plain text
                    try:
                        html_message = render_to_string('emails/orders/order_reminder.html', context)
                    except:
                        html_message = None
                    
                    # Simple text message
                    text_message = f"""
                    Dear {context['customer_name']},
                    
                    This is a reminder that your order #{context['order_number']} 
                    placed on {context['order_date']} is still {context['status']}.
                    
                    Please contact us if you need any assistance.
                    
                    Best regards,
                    {settings.SITE_NAME}
                    """
                    
                    send_mail(
                        subject=f"Reminder: Order #{order_data['order_number']} is still {order_data['status']}",
                        message=text_message.strip(),
                        html_message=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order_data['customer__email']],
                        fail_silently=True,
                    )
                    total_sent += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send reminder for order {order_data['order_number']}: {e}")
                    failed_emails.append(order_data['order_number'])
        
        # Mark as sent today
        cache.set(cache_key, True, 86400)  # Cache for 24 hours
        
        result = f"Sent {total_sent} order reminder emails"
        if failed_emails:
            result += f" (Failed: {len(failed_emails)})"
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in order reminder task: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def update_product_sales_stats(self):
    """
    Optimized product sales statistics update with batch processing.
    """
    try:
        from products.models import Product
        
        # Check cache
        cache_key = "product_sales_stats:last_update"
        last_update = cache.get(cache_key)
        
        # Get completed orders since last update
        query = OrderItem.objects.filter(order__status='completed')
        if last_update:
            query = query.filter(order__updated_at__gt=last_update)
        
        # Aggregate data efficiently
        sales_data = query.values('product').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        ).order_by('product')
        
        if not sales_data.exists():
            return "No new sales data to process"
        
        # Batch update products
        with transaction.atomic():
            batch_size = 100
            products_to_update = []
            
            # Get all product IDs in one query
            product_ids = [item['product'] for item in sales_data]
            existing_products = {
                p.id: p for p in Product.objects.filter(id__in=product_ids)
            }
            
            for item in sales_data:
                product = existing_products.get(item['product'])
                if product:
                    # Update sales stats
                    product.total_sales = (product.total_sales or 0) + item['total_quantity']
                    product.total_revenue = (product.total_revenue or 0) + item['total_revenue']
                    products_to_update.append(product)
                    
                    # Batch update when reaching size limit
                    if len(products_to_update) >= batch_size:
                        Product.objects.bulk_update(
                            products_to_update,
                            ['total_sales', 'total_revenue'],
                            batch_size=batch_size
                        )
                        products_to_update = []
            
            # Update remaining products
            if products_to_update:
                Product.objects.bulk_update(
                    products_to_update,
                    ['total_sales', 'total_revenue'],
                    batch_size=batch_size
                )
        
        # Update cache with current timestamp
        cache.set(cache_key, timezone.now(), None)  # No expiry
        
        # Clear product caches
        cache.delete_pattern('product_stats_*')
        
        return f"Updated sales statistics for {len(product_ids)} products"
        
    except Exception as exc:
        logger.error(f"Error updating product sales stats: {exc}")
        raise self.retry(exc=exc, countdown=600)


@shared_task(bind=True, max_retries=3)
def cancel_abandoned_orders(self, days=7):
    """
    Optimized task to cancel abandoned orders with batch processing.
    """
    try:
        # Check if already run today
        cache_key = f"cancel_abandoned:{days}:{timezone.now().date()}"
        if cache.get(cache_key):
            logger.info("Abandoned order cancellation already run today")
            return "Already processed today"
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get abandoned orders efficiently
        abandoned_orders = Order.objects.filter(
            created_at__lt=cutoff_date,
            status='pending'
        ).values_list('id', flat=True)
        
        order_ids = list(abandoned_orders)
        
        if not order_ids:
            cache.set(cache_key, True, 86400)
            return "No abandoned orders found"
        
        # Batch update orders
        with transaction.atomic():
            batch_size = 100
            total_cancelled = 0
            cancel_note = f"\nAutomatically cancelled due to inactivity after {days} days."
            
            for i in range(0, len(order_ids), batch_size):
                batch_ids = order_ids[i:i + batch_size]
                
                # Update orders in batch
                orders_to_update = []
                for order in Order.objects.filter(id__in=batch_ids):
                    order.status = 'cancelled'
                    order.notes = (order.notes or '') + cancel_note
                    orders_to_update.append(order)
                
                # Bulk update
                Order.objects.bulk_update(
                    orders_to_update,
                    ['status', 'notes'],
                    batch_size=batch_size
                )
                
                total_cancelled += len(batch_ids)
                logger.info(f"Cancelled {total_cancelled} orders so far")
                
                # Update product stock for cancelled items
                self._restore_stock_for_cancelled_orders(batch_ids)
        
        # Mark as processed today
        cache.set(cache_key, True, 86400)
        
        # Clear order caches
        cache.delete_pattern('order_*')
        
        return f"Cancelled {total_cancelled} abandoned orders"
        
    except Exception as exc:
        logger.error(f"Error cancelling abandoned orders: {exc}")
        raise self.retry(exc=exc, countdown=900)
    
    def _restore_stock_for_cancelled_orders(self, order_ids):
        """Restore stock for cancelled orders."""
        from products.models import Product, StockMovement
        
        try:
            # Get all items from cancelled orders
            items = OrderItem.objects.filter(
                order_id__in=order_ids
            ).select_related('product')
            
            # Prepare stock movements
            movements = []
            products_to_update = []
            
            for item in items:
                # Restore stock
                item.product.current_stock += item.quantity
                products_to_update.append(item.product)
                
                # Create stock movement record
                movements.append(
                    StockMovement(
                        product=item.product,
                        movement_type='return',
                        quantity=item.quantity,
                        reference=f"Order cancelled: {item.order.order_number}",
                        created_by=None  # System action
                    )
                )
            
            # Bulk update products
            if products_to_update:
                Product.objects.bulk_update(
                    products_to_update,
                    ['current_stock'],
                    batch_size=100
                )
            
            # Bulk create movements
            if movements:
                StockMovement.objects.bulk_create(movements, batch_size=100)
                
        except Exception as e:
            logger.error(f"Error restoring stock: {e}")


@shared_task
def generate_daily_order_summary():
    """Generate daily order summary report."""
    try:
        today = timezone.now().date()
        cache_key = f"daily_order_summary:{today}"
        
        # Check cache
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get today's orders
        today_start = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        today_end = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.max.time())
        )
        
        orders = Order.objects.filter(
            created_at__range=(today_start, today_end)
        )
        
        # Generate summary
        summary = {
            'date': today.isoformat(),
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(
                total=Sum(F('total_amount'))
            )['total'] or 0,
            'orders_by_status': dict(
                orders.values('status').annotate(
                    count=models.Count('id')
                ).values_list('status', 'count')
            ),
            'top_products': list(
                OrderItem.objects.filter(
                    order__in=orders
                ).values('product__name').annotate(
                    quantity=Sum('quantity'),
                    revenue=Sum(F('price') * F('quantity'))
                ).order_by('-revenue')[:5]
            )
        }
        
        # Cache result
        cache.set(cache_key, summary, 86400)
        
        # Send email to admins if configured
        if getattr(settings, 'SEND_DAILY_SUMMARIES', False):
            from accounts.models import User
            admin_emails = User.objects.filter(
                is_staff=True, is_active=True
            ).values_list('email', flat=True)
            
            if admin_emails:
                send_mail(
                    subject=f"Daily Order Summary - {today}",
                    message=self._format_summary_text(summary),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=list(admin_emails),
                    fail_silently=True,
                )
        
        return summary
        
    except Exception as exc:
        logger.error(f"Error generating daily summary: {exc}")
        return None
    
    def _format_summary_text(self, summary):
        """Format summary data as text."""
        return f"""
        Daily Order Summary for {summary['date']}
        
        Total Orders: {summary['total_orders']}
        Total Revenue: ${summary['total_revenue']:.2f}
        
        Orders by Status:
        {chr(10).join(f"- {status}: {count}" for status, count in summary['orders_by_status'].items())}
        
        Top 5 Products:
        {chr(10).join(f"- {p['product__name']}: {p['quantity']} units (${p['revenue']:.2f})" for p in summary['top_products'])}
        """