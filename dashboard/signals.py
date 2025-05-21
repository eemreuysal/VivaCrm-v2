"""
Signal handlers for the Dashboard app.

This module defines signal handlers that keep dashboard data updated
when related models change. It uses post_save and post_delete signals
to trigger Celery tasks that update dashboard caches.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.conf import settings

from products.models import Product, StockMovement
from orders.models import Order, OrderItem
from customers.models import Customer
from invoices.models import Invoice

from .tasks import update_dashboard_on_data_change

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Product)
def product_change_handler(sender, instance, **kwargs):
    """
    Handle changes to Product model to update dashboard data.
    
    This handler is triggered when a product is created, updated, or deleted.
    It dispatches a task to update the dashboard caches related to products.
    
    Args:
        sender: The model class (always Product)
        instance: The Product instance that was changed
        kwargs: Signal keywords including 'created'
    """
    logger.debug(f"Product change detected (ID: {instance.id}), updating dashboard")
    update_dashboard_on_data_change.delay('Product', instance.id)


from django.db.models.signals import pre_save
from django.db import transaction

@receiver(pre_save, sender=Product)
def product_stock_change_handler(sender, instance, **kwargs):
    """
    Handle product stock changes to update dashboard data.
    
    This handler is specifically for stock quantity changes.
    It compares the old and new stock quantity values to
    detect changes and update dashboard caches accordingly.
    
    Args:
        sender: The model class (always Product)
        instance: The Product instance being saved
        kwargs: Signal keywords
    """
    try:
        # Eski ürün durumunu al (veritabanından)
        if instance.pk:
            old_instance = Product.objects.get(pk=instance.pk)
            # Sadece stok değişmişse dashboard'u güncelle
            if old_instance.stock != instance.stock:
                logger.debug(f"Product stock changed for ID: {instance.id} from {old_instance.stock} to {instance.stock}")
                # İşlem sonrasında çalıştırılmak üzere transaction.on_commit kullan
                transaction.on_commit(
                    lambda: update_dashboard_on_data_change.delay('ProductStock', instance.id)
                )
    except Product.DoesNotExist:
        # Yeni ürün oluşturuluyor, sinyal zaten post_save ile yakalanacak
        pass


@receiver([post_save, post_delete], sender=StockMovement)
def stock_movement_change_handler(sender, instance, **kwargs):
    """
    Handle changes to StockMovement model to update dashboard data.
    
    This handler is triggered when a stock movement is created, updated, or deleted.
    It updates dashboard caches related to product stock levels.
    
    Args:
        sender: The model class (always StockMovement)
        instance: The StockMovement instance that was changed
        kwargs: Signal keywords including 'created'
    """
    logger.debug(f"Stock movement detected for product {instance.product_id}, updating dashboard")
    # First update the specific product
    update_dashboard_on_data_change.delay('Product', instance.product_id)
    # Then update stock charts
    update_dashboard_on_data_change.delay('StockMovement', instance.id)


@receiver([post_save, post_delete], sender=Order)
@receiver([post_save, post_delete], sender=OrderItem)
def order_change_handler(sender, instance, **kwargs):
    """
    Handle changes to Order or OrderItem models to update dashboard data.
    
    This handler is triggered when an order or order item is created, updated, or deleted.
    It updates dashboard caches related to orders and sales.
    
    Args:
        sender: The model class (Order or OrderItem)
        instance: The instance that was changed
        kwargs: Signal keywords including 'created'
    """
    model_name = sender.__name__
    logger.debug(f"{model_name} change detected, updating dashboard")
    
    if model_name == 'OrderItem':
        # For OrderItem changes, we also want to update the parent Order
        order_id = instance.order_id
        update_dashboard_on_data_change.delay('Order', order_id)
    else:
        # For Order changes
        update_dashboard_on_data_change.delay('Order', instance.id)


@receiver(pre_save, sender=Order)
def order_status_change_handler(sender, instance, **kwargs):
    """
    Track order status changes and update relevant dashboard data.
    
    This handler is specifically for order status changes.
    It compares the old and new status values to trigger
    appropriate dashboard updates.
    
    Args:
        sender: The model class (always Order)
        instance: The Order instance being saved
        kwargs: Signal keywords
    """
    try:
        # Önceki durumu veritabanından al
        if instance.pk:
            old_instance = Order.objects.get(pk=instance.pk)
            
            # Sadece sipariş durumu değişmişse özel işlem yap
            if old_instance.status != instance.status:
                logger.debug(f"Order status changed for ID: {instance.id} from '{old_instance.status}' to '{instance.status}'")
                
                # İşlem tamamlandıktan sonra çalıştır
                transaction.on_commit(
                    lambda: update_dashboard_on_data_change.delay('OrderStatus', instance.id)
                )
                
                # Sipariş tamamlandıysa, satış istatistiklerini güncelle
                if instance.status in ['completed', 'delivered']:
                    transaction.on_commit(
                        lambda: update_dashboard_on_data_change.delay('CompletedOrder', instance.id)
                    )
                
                # Sipariş iptal edildiyse, iptal istatistiklerini güncelle
                elif instance.status in ['cancelled', 'refunded']:
                    transaction.on_commit(
                        lambda: update_dashboard_on_data_change.delay('CancelledOrder', instance.id)
                    )
    
    except Order.DoesNotExist:
        # Yeni ürün oluşturuluyor, sinyal zaten post_save ile yakalanacak
        pass


@receiver([post_save, post_delete], sender=Customer)
def customer_change_handler(sender, instance, **kwargs):
    """
    Handle changes to Customer model to update dashboard data.
    
    This handler is triggered when a customer is created, updated, or deleted.
    It updates dashboard caches related to customer statistics.
    
    Args:
        sender: The model class (always Customer)
        instance: The Customer instance that was changed
        kwargs: Signal keywords including 'created'
    """
    logger.debug(f"Customer change detected (ID: {instance.id}), updating dashboard")
    update_dashboard_on_data_change.delay('Customer', instance.id)


@receiver([post_save, post_delete], sender=Invoice)
def invoice_change_handler(sender, instance, **kwargs):
    """
    Handle changes to Invoice model to update dashboard data.
    
    This handler is triggered when an invoice is created, updated, or deleted.
    It updates dashboard caches related to sales and financial statistics.
    
    Args:
        sender: The model class (always Invoice)
        instance: The Invoice instance that was changed
        kwargs: Signal keywords including 'created'
    """
    logger.debug(f"Invoice change detected (ID: {instance.id}), updating dashboard")
    update_dashboard_on_data_change.delay('Invoice', instance.id)