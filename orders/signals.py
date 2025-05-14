from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, OrderItem, Payment, Shipment


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_on_item_change(sender, instance, **kwargs):
    """
    Update order totals when an order item is added, updated or deleted
    """
    instance.order.calculate_totals()


@receiver(post_save, sender=Payment)
def update_order_payment_status(sender, instance, created, **kwargs):
    """
    Update order payment status when a payment is added or updated
    """
    order = instance.order
    
    # Get total paid amount for successful payments
    total_paid = sum(
        payment.amount 
        for payment in order.payments.filter(is_successful=True)
    )
    
    # Determine payment status
    if total_paid <= 0:
        payment_status = 'pending'
    elif total_paid >= order.total_amount:
        payment_status = 'paid'
    else:
        payment_status = 'partially_paid'
    
    # Update order if status changed
    if order.payment_status != payment_status:
        order.payment_status = payment_status
        order.save(update_fields=['payment_status'])
        
        # If fully paid and status is pending, move to processing
        if payment_status == 'paid' and order.status == 'pending':
            order.status = 'processing'
            order.save(update_fields=['status'])


@receiver(post_save, sender=Shipment)
def update_order_on_shipment(sender, instance, created, **kwargs):
    """
    Update order status when a shipment is added or updated
    """
    order = instance.order
    
    # Update order shipping/delivery dates based on shipment
    if instance.status == 'shipped' and not order.shipping_date:
        order.shipping_date = instance.shipping_date
        order.status = 'shipped'
        order.save(update_fields=['shipping_date', 'status'])
    
    if instance.status == 'delivered' and not order.delivery_date:
        order.delivery_date = instance.actual_delivery
        order.status = 'delivered'
        order.save(update_fields=['delivery_date', 'status'])
        
        # If delivered and paid, mark as completed
        if order.payment_status == 'paid':
            order.status = 'completed'
            order.save(update_fields=['status'])