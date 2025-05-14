"""
Signal handlers for cache invalidation.

This module contains signal handlers that clear cache when models are updated.
"""
import logging
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache

# Import models
from products.models import Product, Category, StockMovement
from customers.models import Customer, Address, Contact
from orders.models import Order, OrderItem, Payment, Shipment
from invoices.models import Invoice, InvoiceItem
from core.cache import invalidate_cache_prefix

logger = logging.getLogger(__name__)


# Product-related signals
@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalidate product-related caches when a product is saved or deleted."""
    logger.debug(f"Invalidating product cache for {instance}")
    invalidate_cache_prefix(f"product:{instance.pk}")
    invalidate_cache_prefix("dashboard:low_stock_products")
    invalidate_cache_prefix("products:")
    
    # Invalidate dashboard charts
    invalidate_cache_prefix("dashboard:chart:products")


@receiver([post_save, post_delete], sender=StockMovement)
def invalidate_stock_cache(sender, instance, **kwargs):
    """Invalidate stock-related caches when stock movement occurs."""
    logger.debug(f"Invalidating stock cache for product {instance.product_id}")
    invalidate_cache_prefix(f"product:{instance.product_id}")
    invalidate_cache_prefix("dashboard:low_stock_products")


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidate category-related caches when a category is saved or deleted."""
    logger.debug(f"Invalidating category cache for {instance}")
    invalidate_cache_prefix(f"category:{instance.pk}")
    invalidate_cache_prefix("categories:")


# Customer-related signals
@receiver([post_save, post_delete], sender=Customer)
def invalidate_customer_cache(sender, instance, **kwargs):
    """Invalidate customer-related caches when a customer is saved or deleted."""
    logger.debug(f"Invalidating customer cache for {instance}")
    invalidate_cache_prefix(f"customer:{instance.pk}")
    invalidate_cache_prefix("customers:")
    invalidate_cache_prefix("dashboard:stats")  # Total customer count


@receiver([post_save, post_delete], sender=Address)
def invalidate_address_cache(sender, instance, **kwargs):
    """Invalidate address-related caches when an address is saved or deleted."""
    logger.debug(f"Invalidating address cache for customer {instance.customer_id}")
    invalidate_cache_prefix(f"customer:{instance.customer_id}")
    invalidate_cache_prefix(f"address:{instance.pk}")


@receiver([post_save, post_delete], sender=Contact)
def invalidate_contact_cache(sender, instance, **kwargs):
    """Invalidate contact-related caches when a contact is saved or deleted."""
    logger.debug(f"Invalidating contact cache for customer {instance.customer_id}")
    invalidate_cache_prefix(f"customer:{instance.customer_id}")
    invalidate_cache_prefix(f"contact:{instance.pk}")


# Order-related signals
@receiver([post_save, post_delete], sender=Order)
def invalidate_order_cache(sender, instance, **kwargs):
    """Invalidate order-related caches when an order is saved or deleted."""
    logger.debug(f"Invalidating order cache for {instance}")
    invalidate_cache_prefix(f"order:{instance.pk}")
    invalidate_cache_prefix("orders:")
    invalidate_cache_prefix("dashboard:stats")  # For order stats
    invalidate_cache_prefix("dashboard:chart:sales")  # For sales charts


@receiver([post_save, post_delete], sender=OrderItem)
def invalidate_order_item_cache(sender, instance, **kwargs):
    """Invalidate order item-related caches when an order item is saved or deleted."""
    logger.debug(f"Invalidating order item cache for order {instance.order_id}")
    invalidate_cache_prefix(f"order:{instance.order_id}")
    invalidate_cache_prefix(f"product:{instance.product_id}")
    invalidate_cache_prefix("dashboard:chart:products")  # For product charts


@receiver([post_save, post_delete], sender=Payment)
def invalidate_payment_cache(sender, instance, **kwargs):
    """Invalidate payment-related caches when a payment is saved or deleted."""
    logger.debug(f"Invalidating payment cache for order {instance.order_id}")
    invalidate_cache_prefix(f"order:{instance.order_id}")
    invalidate_cache_prefix(f"payment:{instance.pk}")
    invalidate_cache_prefix("dashboard:stats")  # For revenue stats


# Invoice-related signals
@receiver([post_save, post_delete], sender=Invoice)
def invalidate_invoice_cache(sender, instance, **kwargs):
    """Invalidate invoice-related caches when an invoice is saved or deleted."""
    logger.debug(f"Invalidating invoice cache for {instance}")
    invalidate_cache_prefix(f"invoice:{instance.pk}")
    invalidate_cache_prefix("invoices:")
    
    # If order is associated, invalidate order cache too
    if instance.order:
        invalidate_cache_prefix(f"order:{instance.order.pk}")


@receiver([post_save, post_delete], sender=InvoiceItem)
def invalidate_invoice_item_cache(sender, instance, **kwargs):
    """Invalidate invoice item-related caches when an invoice item is saved or deleted."""
    logger.debug(f"Invalidating invoice item cache for invoice {instance.invoice_id}")
    invalidate_cache_prefix(f"invoice:{instance.invoice_id}")
    
    # If product is associated, invalidate product cache too
    if instance.product:
        invalidate_cache_prefix(f"product:{instance.product.pk}")


# Dashboard stats invalidation
def invalidate_dashboard_caches():
    """Invalidate all dashboard-related caches."""
    logger.info("Invalidating all dashboard caches")
    invalidate_cache_prefix("dashboard:")