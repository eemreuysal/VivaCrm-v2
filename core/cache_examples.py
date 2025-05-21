"""
VivaCRM v2 Cache Kullanım Örnekleri

Bu dosya, projede önbellekleme sisteminin nasıl kullanılacağına dair örnekler içerir.
"""
from django.core.cache import cache
from core.cache import (
    cache_method, 
    cache_function, 
    cache_view,
    cache_viewset_action,
    invalidate_cache_prefix,
    generate_cache_key
)
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets


# 1. Basit cache kullanımı
def get_expensive_calculation():
    """Yoğun hesaplama yapan bir fonksiyon"""
    cache_key = "expensive_calculation"
    
    # Cache'den al
    result = cache.get(cache_key)
    if result is not None:
        return result
    
    # Hesapla ve cache'e kaydet
    result = perform_expensive_calculation()
    cache.set(cache_key, result, timeout=3600)  # 1 saat
    return result


# 2. Cache dekoratörü ile fonksiyon önbellekleme
@cache_function(timeout=1800)  # 30 dakika
def get_product_statistics():
    """Ürün istatistiklerini hesaplar"""
    from products.models import Product
    return {
        'total': Product.objects.count(),
        'active': Product.objects.filter(is_active=True).count(),
        'in_stock': Product.objects.filter(stock__gt=0).count(),
    }


# 3. Cache dekoratörü ile method önbellekleme
class ProductService:
    @cache_method(timeout=3600, key_prefix="product_service")
    def get_low_stock_products(self, threshold=10):
        """Düşük stoklu ürünleri getirir"""
        from products.models import Product
        return Product.objects.filter(stock__lt=threshold)


# 4. View cache kullanımı
@cache_page(60 * 15)  # 15 dakika
def public_product_list(request):
    """Herkese açık ürün listesi - önbelleğe alınır"""
    # View logic here
    pass


# 5. ViewSet action cache kullanımı
class ProductViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['get'])
    @cache_viewset_action(timeout=1800, include_request_user=True)
    def popular_products(self, request):
        """Popüler ürünleri kullanıcı bazlı önbelleğe alır"""
        # Action logic here
        return Response({'products': []})
    
    @action(detail=True, methods=['get'])
    @cache_viewset_action(timeout=3600, key_prefix="product_stats")
    def statistics(self, request, pk=None):
        """Ürün istatistiklerini önbelleğe alır"""
        product = self.get_object()
        stats = self._calculate_product_stats(product)
        return Response(stats)


# 6. Model bazlı cache yönetimi
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class CachedProduct(models.Model):
    """Cache yönetimi ile ürün modeli"""
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    
    @property
    def cache_key(self):
        """Model için benzersiz cache key"""
        return f"product:{self.pk}"
    
    def get_from_cache(self):
        """Modeli cache'den getir"""
        return cache.get(self.cache_key)
    
    def set_to_cache(self, timeout=3600):
        """Modeli cache'e kaydet"""
        cache.set(self.cache_key, self, timeout)
    
    def invalidate_cache(self):
        """Model cache'ini temizle"""
        cache.delete(self.cache_key)
        # İlgili prefix'leri de temizle
        invalidate_cache_prefix(f"product_list")
        invalidate_cache_prefix(f"product_stats:{self.pk}")


# 7. Signal tabanlı cache invalidation
@receiver(post_save, sender=CachedProduct)
def invalidate_product_cache_on_save(sender, instance, **kwargs):
    """Ürün kaydedildiğinde cache'i temizle"""
    instance.invalidate_cache()
    # Dashboard cache'ini de temizle
    invalidate_cache_prefix("dashboard:stats")


@receiver(post_delete, sender=CachedProduct)
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    """Ürün silindiğinde cache'i temizle"""
    instance.invalidate_cache()
    invalidate_cache_prefix("dashboard:stats")


# 8. Conditional caching örneği
def conditional_cache_view(request):
    """Koşullu önbellekleme örneği"""
    # Kullanıcı giriş yapmışsa önbellekleme
    if request.user.is_authenticated:
        return render(request, 'template.html', context)
    
    # Giriş yapmamış kullanıcılar için önbelleğe al
    cache_key = generate_cache_key('public_view', request.path)
    cached_response = cache.get(cache_key)
    
    if cached_response:
        return cached_response
    
    response = render(request, 'template.html', context)
    cache.set(cache_key, response, timeout=600)  # 10 dakika
    return response


# 9. Cache warming (ısıtma) örneği
def warm_product_cache():
    """Önemli cache'leri önceden yükle"""
    from products.models import Product
    
    # En çok satılan ürünleri cache'e al
    top_products = Product.objects.filter(
        is_active=True
    ).order_by('-sales_count')[:20]
    
    for product in top_products:
        cache_key = f"product:{product.pk}"
        cache.set(cache_key, product, timeout=7200)  # 2 saat
    
    # Kategori istatistiklerini cache'e al
    from products.models import Category
    for category in Category.objects.all():
        stats = calculate_category_stats(category)
        cache_key = f"category_stats:{category.pk}"
        cache.set(cache_key, stats, timeout=3600)  # 1 saat


# 10. Cache monitoring örneği
def get_cache_statistics():
    """Cache kullanım istatistiklerini getir"""
    import redis
    from django.conf import settings
    
    # Redis bağlantısı
    r = redis.from_url(settings.CACHES['default']['LOCATION'])
    
    # Cache istatistikleri
    info = r.info('stats')
    
    return {
        'total_keys': r.dbsize(),
        'hits': info.get('keyspace_hits', 0),
        'misses': info.get('keyspace_misses', 0),
        'hit_rate': calculate_hit_rate(info),
        'memory_used': info.get('used_memory_human', 'N/A'),
        'connected_clients': info.get('connected_clients', 0),
    }


# 11. Batch cache operations
def batch_cache_operations():
    """Toplu cache işlemleri"""
    from django.core.cache import cache
    
    # Birden fazla değeri aynı anda kaydet
    cache.set_many({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
    }, timeout=3600)
    
    # Birden fazla değeri aynı anda getir
    values = cache.get_many(['key1', 'key2', 'key3'])
    
    # Belirli bir pattern'e uyan key'leri sil
    from core.cache import invalidate_cache_prefix
    invalidate_cache_prefix('product:')  # product: ile başlayan tüm key'leri sil


def calculate_hit_rate(info):
    """Cache hit oranını hesapla"""
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    total = hits + misses
    
    if total == 0:
        return 0
    
    return round((hits / total) * 100, 2)