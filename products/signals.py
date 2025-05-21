"""
Products modülü için Django signals.
Model event'leri için reaksiyon tanımlamaları.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.cache import cache

from .models import Product, Category, ProductFamily, ProductImage, StockMovement
from .services import StockService
import logging

logger = logging.getLogger(__name__)


# ------------ Pre Save Signals ------------

@receiver(pre_save, sender=Product)
def prepare_product_for_save(sender, instance, **kwargs):
    """Product save öncesi işlemleri"""
    from .services import ProductService
    ProductService.prepare_product_for_save(instance)


@receiver(pre_save, sender=Category)
def prepare_category_for_save(sender, instance, **kwargs):
    """Category save öncesi işlemleri"""
    from .services import SlugService
    if not instance.slug:
        instance.slug = SlugService.generate_slug(instance.name, Category, instance)


@receiver(pre_save, sender=ProductFamily)
def prepare_family_for_save(sender, instance, **kwargs):
    """ProductFamily save öncesi işlemleri"""
    from .services import SlugService
    if not instance.slug:
        instance.slug = SlugService.generate_slug(instance.name, ProductFamily, instance)


@receiver(pre_save, sender=StockMovement)
def prepare_stock_movement_for_save(sender, instance, **kwargs):
    """StockMovement save öncesi işlemleri"""
    # Sadece yeni kayıt ise hazırla
    if not instance.pk:
        StockService.prepare_stock_movement(instance)


# ------------ Post Save Signals ------------

@receiver(post_save, sender=StockMovement)
def update_product_stock(sender, instance, created, **kwargs):
    """
    StockMovement kaydedildiğinde ürün stok bilgisini güncelle.
    """
    if created:
        StockService.update_product_stock(
            product_id=instance.product.id,
            new_stock=instance.new_stock,
            cost=instance.product.cost if instance.unit_cost else None
        )


@receiver(post_save, sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    """
    Product kaydedildiğinde ilgili cache'i temizle.
    """
    # Ürün detay cache'i
    cache.delete(f'product_{instance.id}')
    
    # Kategori ürünleri cache'i
    if instance.category:
        cache.delete(f'category_products_{instance.category.id}')
    
    # Aile ürünleri cache'i
    if instance.family:
        cache.delete(f'family_products_{instance.family.id}')
    
    # Düşük stok cache'i
    if instance.stock <= instance.threshold_stock:
        cache.delete('products_low_stock')


@receiver(post_save, sender=ProductImage)
def handle_primary_image(sender, instance, created, **kwargs):
    """
    Bir ürün görseli primary olarak işaretlendiğinde, 
    aynı ürünün diğer primary görsellerini kaldır.
    """
    if instance.is_primary:
        # Bu görsel hariç aynı ürünün diğer primary görsellerini bul
        other_primary_images = ProductImage.objects.filter(
            product=instance.product,
            is_primary=True
        ).exclude(id=instance.id)
        
        # Primary işaretlerini kaldır
        if other_primary_images.exists():
            other_primary_images.update(is_primary=False)


# ------------ Delete Signals ------------

# Burada delete sinyalleri eklenebilir