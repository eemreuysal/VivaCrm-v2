from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F
from django.core.cache import cache
from django.db import transaction
from .models import Product, StockMovement
from django.utils import timezone
from datetime import timedelta
import csv
import os
import logging
import json

logger = logging.getLogger(__name__)


class OptimizedTask:
    """Base class for optimized Celery tasks with caching and batching."""
    
    @staticmethod
    def cache_key(task_name, *args, **kwargs):
        """Generate a cache key for task results."""
        parts = [task_name]
        parts.extend(str(arg) for arg in args)
        parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return ":".join(parts)
    
    @staticmethod
    def get_cached_result(task_name, *args, **kwargs):
        """Get cached result if available."""
        cache_key = OptimizedTask.cache_key(task_name, *args, **kwargs)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_result(result, task_name, *args, **kwargs):
        """Cache task result."""
        cache_key = OptimizedTask.cache_key(task_name, *args, **kwargs)
        timeout = getattr(settings, 'CELERY_TASK_CACHE_TIMEOUT', 3600)
        cache.set(cache_key, result, timeout)
        return result


@shared_task(bind=True, max_retries=3)
def check_low_stock_levels(self):
    """
    Optimized task to check for products with low stock levels.
    Returns cached result if available.
    """
    # Check cache first
    cached_result = OptimizedTask.get_cached_result('low_stock_check')
    if cached_result:
        logger.info("Returning cached low stock check result")
        return cached_result
    
    try:
        # Use select_related and values to minimize database queries
        low_stock_products = Product.objects.filter(
            current_stock__lt=F('threshold_stock'),
            threshold_stock__gt=0
        ).select_related('category').values(
            'name', 'sku', 'current_stock', 'threshold_stock', 'category__name'
        )
        
        # Convert to list for better performance
        products_list = list(low_stock_products)
        
        if not products_list:
            result = "No products with low stock found"
            return OptimizedTask.cache_result(result, 'low_stock_check')
        
        # Build email message efficiently
        subject = "Low Stock Alert - Action Required"
        message_lines = ["The following products are below their minimum stock levels:", ""]
        
        # Batch process products
        for product in products_list:
            message_lines.append(
                f"• {product['name']} ({product['sku']}): "
                f"Current stock: {product['current_stock']}, "
                f"Threshold: {product['threshold_stock']}, "
                f"Category: {product['category__name']}"
            )
        
        message_lines.extend(["", "Please restock these items as soon as possible."])
        message = "\n".join(message_lines)
        
        # Get staff emails efficiently
        from accounts.models import User
        staff_emails = list(User.objects.filter(
            is_staff=True, is_active=True
        ).values_list('email', flat=True))
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=staff_emails,
            fail_silently=False,
        )
        
        result = f"Sent low stock alerts for {len(products_list)} products"
        return OptimizedTask.cache_result(result, 'low_stock_check')
        
    except Exception as exc:
        logger.error(f"Error checking low stock levels: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def generate_stock_movements_report(self):
    """
    Optimized stock movements report generation with batch processing.
    """
    try:
        # Define time period
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Check if recent report already exists
        cache_key = f"stock_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        cached_path = cache.get(cache_key)
        if cached_path and os.path.exists(cached_path):
            logger.info("Returning cached stock report")
            return f"Stock movements report already exists at {cached_path}"
        
        # Query movements with optimized select_related
        movements = StockMovement.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related(
            'product', 'created_by'
        ).values(
            'created_at', 'product__name', 'product__sku',
            'movement_type', 'quantity', 'reference',
            'created_by__first_name', 'created_by__last_name'
        )
        
        # Create reports directory
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate CSV file with batch processing
        filename = f"stock_movements_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w', newline='', buffering=8192) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Date', 'Product', 'SKU', 'Type', 'Quantity', 'Reference', 'User'])
            
            # Process in batches
            batch_size = 1000
            for i in range(0, movements.count(), batch_size):
                batch = movements[i:i + batch_size]
                rows = []
                
                for movement in batch:
                    user_name = f"{movement['created_by__first_name']} {movement['created_by__last_name']}" \
                               if movement['created_by__first_name'] else 'System'
                    
                    rows.append([
                        movement['created_at'].strftime('%Y-%m-%d %H:%M'),
                        movement['product__name'],
                        movement['product__sku'],
                        movement['movement_type'],
                        movement['quantity'],
                        movement['reference'],
                        user_name
                    ])
                
                writer.writerows(rows)
        
        # Cache the filepath
        cache.set(cache_key, filepath, 86400)  # Cache for 24 hours
        
        return f"Stock movements report generated at {filepath}"
        
    except Exception as exc:
        logger.error(f"Error generating stock report: {exc}")
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=3)
def expire_product_promotions(self):
    """
    Optimized task to expire product promotions with batch processing.
    """
    try:
        # Use transaction for consistency
        with transaction.atomic():
            # Find products with expired promotions
            expired_products = Product.objects.filter(
                sale_price__isnull=False,
                sale_end_date__lt=timezone.now()
            ).values_list('id', flat=True)
            
            # Convert to list for batch processing
            product_ids = list(expired_products)
            
            if not product_ids:
                return "No expired promotions found"
            
            # Batch update products
            batch_size = 500
            total_updated = 0
            
            for i in range(0, len(product_ids), batch_size):
                batch_ids = product_ids[i:i + batch_size]
                
                # Use bulk_update for better performance
                products_to_update = Product.objects.filter(id__in=batch_ids)
                for product in products_to_update:
                    product.sale_price = None
                    product.sale_end_date = None
                
                # Bulk update
                Product.objects.bulk_update(
                    products_to_update,
                    ['sale_price', 'sale_end_date'],
                    batch_size=batch_size
                )
                
                total_updated += len(batch_ids)
                logger.info(f"Updated {total_updated} products so far")
            
            # Clear relevant caches
            cache.delete_pattern('product_*')
            
            return f"Reset pricing for {total_updated} products with expired promotions"
            
    except Exception as exc:
        logger.error(f"Error expiring promotions: {exc}")
        raise self.retry(exc=exc, countdown=180)


@shared_task(bind=True, max_retries=3)
def bulk_update_stock_levels(self, updates: list):
    """
    Optimized bulk stock update task with batch processing.
    
    Args:
        updates: List of dictionaries with 'sku' and 'quantity' keys
    """
    try:
        # Validate input
        if not updates or not isinstance(updates, list):
            return "No updates provided"
        
        # Batch process updates
        with transaction.atomic():
            batch_size = 100
            total_updated = 0
            errors = []
            
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                
                # Get all SKUs in batch
                skus = [item['sku'] for item in batch]
                
                # Fetch products in batch
                products = {
                    p.sku: p
                    for p in Product.objects.filter(sku__in=skus)
                }
                
                # Prepare stock movements
                movements = []
                
                for update in batch:
                    sku = update.get('sku')
                    quantity = update.get('quantity')
                    
                    if not sku or quantity is None:
                        errors.append(f"Invalid update data: {update}")
                        continue
                    
                    product = products.get(sku)
                    if not product:
                        errors.append(f"Product not found: {sku}")
                        continue
                    
                    # Calculate quantity difference
                    quantity_diff = quantity - product.current_stock
                    
                    if quantity_diff != 0:
                        # Update product stock
                        product.current_stock = quantity
                        product.save(update_fields=['current_stock'])
                        
                        # Create stock movement
                        movements.append(
                            StockMovement(
                                product=product,
                                movement_type='adjustment',
                                quantity=abs(quantity_diff),
                                reference=f"Bulk update - {'increase' if quantity_diff > 0 else 'decrease'}",
                                created_by=None  # System update
                            )
                        )
                        
                        total_updated += 1
                
                # Bulk create stock movements
                if movements:
                    StockMovement.objects.bulk_create(movements, batch_size=batch_size)
            
            # Clear caches
            cache.delete_pattern('product_*')
            cache.delete_pattern('stock_*')
            
            result = f"Updated stock for {total_updated} products"
            if errors:
                result += f" (Errors: {len(errors)})"
                logger.warning(f"Stock update errors: {errors[:10]}")  # Log first 10 errors
            
            return result
            
    except Exception as exc:
        logger.error(f"Error in bulk stock update: {exc}")
        raise self.retry(exc=exc, countdown=300)


# Celery beat schedule için yeni görevler
@shared_task
def cleanup_old_reports():
    """Delete old report files to save storage space."""
    try:
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        if not os.path.exists(reports_dir):
            return "Reports directory does not exist"
        
        # Delete files older than 30 days
        threshold_date = timezone.now() - timedelta(days=30)
        deleted_count = 0
        
        for filename in os.listdir(reports_dir):
            filepath = os.path.join(reports_dir, filename)
            
            # Check file age
            if os.path.isfile(filepath):
                file_time = timezone.datetime.fromtimestamp(
                    os.path.getmtime(filepath),
                    tz=timezone.get_current_timezone()
                )
                
                if file_time < threshold_date:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"Deleted old report: {filename}")
        
        return f"Cleaned up {deleted_count} old report files"
        
    except Exception as exc:
        logger.error(f"Error cleaning up reports: {exc}")
        return f"Error during cleanup: {exc}"


@shared_task(bind=True, max_retries=3)
def import_products_task(self, filename, user_id, import_options=None):
    """
    Celery task for asynchronous product import from Excel files.
    
    Args:
        filename: Name of the uploaded file
        user_id: ID of the user who initiated the import
        import_options: Optional dictionary with import settings
    """
    from django.contrib.auth import get_user_model
    from products.excel_smart_import import import_products_smart
    
    try:
        # Get user
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Get file path
        file_path = os.path.join(settings.MEDIA_ROOT, 'temp', filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Import file not found: {filename}")
        
        logger.info(f"Starting Excel import task for file: {filename}")
        
        # Import products
        with open(file_path, 'rb') as file:
            result = import_products_smart(
                file_buffer=file, 
                user=user,
                show_warnings=import_options.get('show_warnings', False) if import_options else False
            )
        
        # Clean up temp file
        try:
            os.remove(file_path)
        except OSError:
            logger.warning(f"Could not remove temp file: {file_path}")
        
        # Send notification email
        if user.email:
            subject = "Excel Import Completed"
            message = f"""
            Excel import has been completed successfully.
            
            Import Summary:
            - Total products: {result.get('total', 0)}
            - Successfully imported: {result.get('success', 0)}
            - Failed: {result.get('failed', 0)}
            - Skipped: {result.get('skipped', 0)}
            
            Import started by: {user.get_full_name() or user.username}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        
        # Cache the result for retrieval
        cache_key = f"import_result_{self.request.id}"
        cache.set(cache_key, result, 3600)  # Cache for 1 hour
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in import_products_task: {exc}")
        
        # Send error notification
        if user_id:
            try:
                User = get_user_model()
                user = User.objects.get(id=user_id)
                if user.email:
                    send_mail(
                        subject="Excel Import Failed",
                        message=f"Excel import failed with error: {str(exc)}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
            except:
                pass
        
        raise self.retry(exc=exc, countdown=60)