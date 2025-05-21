"""
Orders modülü için Django signals.
Model event'leri için reaksiyon tanımlamaları.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
import logging

from .models import Order, OrderItem, Payment, Shipment
from .services import OrderCalculationService, OrderStatusService

logger = logging.getLogger(__name__)


# ------------ Pre Save Signals ------------

@receiver(pre_save, sender=Order)
def prepare_order_for_save(sender, instance, **kwargs):
    """Order save öncesi işlemleri"""
    from .services import OrderService
    OrderService.prepare_order_for_save(instance)
    
    # Durum değişikliği kontrolü
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            # Durum değişikliği varsa ve geçerli değilse engelle
            if old_instance.status != instance.status:
                if not OrderStatusService.is_valid_status_transition(old_instance.status, instance.status):
                    # Log the invalid transition attempt
                    logger.warning(f"Geçersiz durum geçişi: {old_instance.status} -> {instance.status} (Order: {instance.order_number})")
                    # Restore the old status instead of raising an exception to avoid breaking existing code
                    instance.status = old_instance.status
                    
            # Ödeme durumu değişikliği varsa ve geçerli değilse engelle
            if old_instance.payment_status != instance.payment_status:
                if not OrderStatusService.is_valid_payment_status_transition(old_instance.payment_status, instance.payment_status):
                    # Log the invalid transition attempt
                    logger.warning(f"Geçersiz ödeme durumu geçişi: {old_instance.payment_status} -> {instance.payment_status} (Order: {instance.order_number})")
                    # Restore the old payment status
                    instance.payment_status = old_instance.payment_status
        except Order.DoesNotExist:
            # Yeni kayıt, geçişi kontrol etmeye gerek yok
            pass


# ------------ Post Save Signals ------------

@receiver(post_save, sender=OrderItem)
def update_order_on_item_creation(sender, instance, created, **kwargs):
    """
    Sipariş kalemi eklendiğinde sipariş toplamlarını güncelle
    """
    if created:
        # Sadece yeni eklemeler için çalışsın
        OrderCalculationService.calculate_order_totals(instance.order)


@receiver(post_save, sender=OrderItem)
def update_order_on_item_update(sender, instance, created, **kwargs):
    """
    Sipariş kalemi güncellendiğinde sipariş toplamlarını güncelle
    """
    if not created:
        # Sadece güncellemeler için çalışsın
        OrderCalculationService.calculate_order_totals(instance.order)


@receiver(post_delete, sender=OrderItem)
def update_order_on_item_delete(sender, instance, **kwargs):
    """
    Sipariş kalemi silindiğinde sipariş toplamlarını güncelle
    """
    try:
        # Sipariş hala varsa, toplamları güncelle
        if Order.objects.filter(id=instance.order_id).exists():
            order = Order.objects.get(id=instance.order_id)
            OrderCalculationService.calculate_order_totals(order)
    except Exception as e:
        logger.error(f"Item silme sırasında hata: {str(e)}")


@receiver(post_save, sender=Payment)
def update_order_payment_status(sender, instance, created, **kwargs):
    """
    Ödeme eklendiğinde veya güncellendiğinde sipariş ödeme durumunu güncelle
    """
    order = instance.order
    
    # Başarılı ödemeler için toplam ödenen tutarı hesapla
    total_paid = sum(
        payment.amount 
        for payment in order.payments.filter(is_successful=True)
    )
    
    # Ödeme durumunu belirle
    if total_paid <= 0:
        payment_status = 'pending'
    elif total_paid >= order.total_amount:
        payment_status = 'paid'
    else:
        payment_status = 'partially_paid'
    
    # Durum değişikliği varsa güncelle
    if order.payment_status != payment_status:
        # Durum geçişi geçerli mi?
        if OrderStatusService.is_valid_payment_status_transition(order.payment_status, payment_status):
            old_status = order.payment_status
            order.payment_status = payment_status
            order.save(update_fields=['payment_status', 'updated_at'])
            
            logger.info(f"Ödeme durumu güncellendi: {order.order_number} - {old_status} -> {payment_status}")
            
            # Tam ödenmiş ve durum beklemede ise, işleniyor durumuna geçir
            if payment_status == 'paid' and order.status == 'pending':
                if OrderStatusService.is_valid_status_transition(order.status, 'processing'):
                    order.status = 'processing'
                    order.save(update_fields=['status', 'updated_at'])
                    logger.info(f"Sipariş durumu otomatik güncellendi: {order.order_number} - pending -> processing (tam ödeme sonrası)")


@receiver(post_save, sender=Shipment)
def update_order_on_shipment(sender, instance, created, **kwargs):
    """
    Kargo eklendiğinde veya güncellendiğinde sipariş durumunu güncelle
    """
    order = instance.order
    
    # Kargoya verildi
    if instance.status == 'shipped' and not order.shipping_date:
        # Durum geçişi geçerli mi?
        if OrderStatusService.is_valid_status_transition(order.status, 'shipped'):
            order.shipping_date = instance.shipping_date or timezone.now()
            order.status = 'shipped'
            order.save(update_fields=['shipping_date', 'status', 'updated_at'])
            logger.info(f"Sipariş durumu kargo ile güncellendi: {order.order_number} - {order.status} -> shipped")
    
    # Teslim edildi
    if instance.status == 'delivered' and not order.delivery_date:
        # Durum geçişi geçerli mi?
        if OrderStatusService.is_valid_status_transition(order.status, 'delivered'):
            order.delivery_date = instance.actual_delivery or timezone.now()
            order.status = 'delivered'
            order.save(update_fields=['delivery_date', 'status', 'updated_at'])
            logger.info(f"Sipariş durumu teslimat ile güncellendi: {order.order_number} - {order.status} -> delivered")
            
            # Teslim edildi ve ödendi ise, tamamlandı olarak işaretle
            if order.payment_status == 'paid':
                if OrderStatusService.is_valid_status_transition(order.status, 'completed'):
                    order.status = 'completed'
                    order.save(update_fields=['status', 'updated_at'])
                    logger.info(f"Sipariş durumu otomatik güncellendi: {order.order_number} - delivered -> completed (ödeme tamamlandığı için)")


@receiver(post_save, sender=Order)
def clear_order_cache(sender, instance, **kwargs):
    """
    Sipariş kaydedildiğinde ilgili önbelleği temizle
    """
    # Sipariş detay önbelleği
    cache.delete(f'order_{instance.id}')
    
    # Müşteri siparişleri önbelleği
    cache.delete(f'customer_orders_{instance.customer_id}')
    
    # Durum toplamları önbelleği
    cache.delete('order_status_counts')
    
    # Aylık sipariş toplamları önbelleği
    cache.delete('monthly_order_totals')