"""
VivaCRM v2 Query Optimizasyon Örnekleri

Bu dosya, projede veritabanı sorgularının nasıl optimize edileceğine dair örnekler içerir.
"""
from django.db.models import Prefetch, F, Q, Count, Sum, Avg
from core.query_optimizer import (
    detect_n_plus_1,
    optimize_queryset,
    suggest_queryset_optimization,
    apply_suggested_optimizations,
    log_queries,
    get_optimized_queryset
)


# 1. N+1 Problem Çözümü
class ProductListView:
    def get_queryset_bad(self):
        """N+1 problemi olan queryset"""
        products = Product.objects.all()
        
        # Her ürün için ayrı sorgu yapılacak (N+1 problemi)
        for product in products:
            print(product.category.name)  # +1 sorgu
            print(product.created_by.username)  # +1 sorgu
        
        return products
    
    def get_queryset_good(self):
        """Optimize edilmiş queryset"""
        # select_related ile ilişkili nesneleri tek sorguda getir
        products = Product.objects.select_related(
            'category',
            'created_by'
        ).all()
        
        # Artık ek sorgu yapılmayacak
        for product in products:
            print(product.category.name)  # Ek sorgu yok
            print(product.created_by.username)  # Ek sorgu yok
        
        return products


# 2. Prefetch Related Kullanımı
class OrderDetailView:
    def get_queryset_bad(self):
        """Many-to-many ilişkilerde N+1 problemi"""
        orders = Order.objects.all()
        
        # Her sipariş için ayrı sorgu
        for order in orders:
            for item in order.items.all():  # +1 sorgu
                print(item.product.name)  # +1 sorgu
        
        return orders
    
    def get_queryset_good(self):
        """Prefetch ile optimize edilmiş"""
        # Özel Prefetch nesnesi ile detaylı kontrol
        items_prefetch = Prefetch(
            'items',
            queryset=OrderItem.objects.select_related('product')
        )
        
        orders = Order.objects.prefetch_related(items_prefetch).all()
        
        # Artık ek sorgu yapılmayacak
        for order in orders:
            for item in order.items.all():  # Ek sorgu yok
                print(item.product.name)  # Ek sorgu yok
        
        return orders


# 3. Query Optimization Decorator
@log_queries
def get_customer_report():
    """Query sayısını logla"""
    customers = Customer.objects.select_related(
        'assigned_to'
    ).prefetch_related(
        'orders',
        'orders__items',
        'orders__items__product'
    ).filter(
        is_active=True
    ).annotate(
        total_orders=Count('orders'),
        total_spent=Sum('orders__total')
    )
    
    return customers


# 4. Otomatik Optimizasyon Önerisi
def optimize_product_queryset():
    """Queryset için optimizasyon önerileri al"""
    # Optimize edilmemiş queryset
    queryset = Product.objects.filter(is_active=True)
    
    # N+1 problemi tespiti
    detection_result = detect_n_plus_1(queryset)
    print(f"N+1 Problem: {detection_result['has_n_plus_1']}")
    print(f"Query Count: {detection_result['total_query_count']}")
    
    # Optimizasyon önerileri
    suggestions = suggest_queryset_optimization(queryset)
    print(f"Öneriler: {suggestions}")
    
    # Önerileri otomatik uygula
    optimized_queryset = apply_suggested_optimizations(queryset)
    
    return optimized_queryset


# 5. Complex Query Optimization
class DashboardView:
    def get_statistics(self):
        """Karmaşık istatistik sorguları"""
        from django.db.models import Case, When, IntegerField
        from django.utils import timezone
        from datetime import timedelta
        
        # Tek sorguda birden fazla istatistik
        stats = Order.objects.aggregate(
            total_orders=Count('id'),
            pending_orders=Count(
                Case(
                    When(status='pending', then=1),
                    output_field=IntegerField()
                )
            ),
            completed_orders=Count(
                Case(
                    When(status='completed', then=1),
                    output_field=IntegerField()
                )
            ),
            total_revenue=Sum(
                Case(
                    When(status='completed', then=F('total')),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            average_order_value=Avg(
                Case(
                    When(status='completed', then=F('total')),
                    output_field=IntegerField()
                )
            ),
            recent_orders=Count(
                Case(
                    When(
                        created_at__gte=timezone.now() - timedelta(days=7),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            )
        )
        
        return stats


# 6. Conditional Select/Prefetch
def get_orders_with_conditional_prefetch(user):
    """Koşullu prefetch kullanımı"""
    # Sadece aktif ürünleri prefetch et
    active_items_prefetch = Prefetch(
        'items',
        queryset=OrderItem.objects.filter(
            product__is_active=True
        ).select_related('product'),
        to_attr='active_items'
    )
    
    # Kullanıcıya göre filtreleme
    if user.is_staff:
        orders = Order.objects.all()
    else:
        orders = Order.objects.filter(customer__owner=user)
    
    # Optimize edilmiş queryset
    return orders.select_related(
        'customer',
        'shipping_address'
    ).prefetch_related(
        active_items_prefetch,
        'payments'
    )


# 7. Queryset Caching Pattern
class CachedQuerysetMixin:
    """Queryset sonuçlarını önbelleğe alan mixin"""
    
    def get_queryset(self):
        """Cache'li queryset"""
        from django.core.cache import cache
        from core.cache import generate_cache_key
        
        # Cache key oluştur
        cache_key = generate_cache_key(
            'queryset',
            self.__class__.__name__,
            self.request.user.id if hasattr(self, 'request') else None
        )
        
        # Cache'den al
        cached_queryset = cache.get(cache_key)
        if cached_queryset is not None:
            return cached_queryset
        
        # Queryset'i optimize et
        queryset = super().get_queryset()
        
        # Model ismine göre otomatik optimizasyon
        model_name = queryset.model.__name__
        queryset = get_optimized_queryset(model_name, queryset)
        
        # Cache'e kaydet
        cache.set(cache_key, queryset, timeout=300)  # 5 dakika
        
        return queryset


# 8. Bulk Operations
def bulk_operations_example():
    """Toplu işlemler için örnekler"""
    from products.models import Product
    
    # Bulk create - Tek sorguda birden fazla kayıt oluştur
    products = [
        Product(name=f"Product {i}", price=i*10)
        for i in range(1000)
    ]
    Product.objects.bulk_create(products, batch_size=100)
    
    # Bulk update - Tek sorguda birden fazla kayıt güncelle
    products = Product.objects.filter(category_id=1)
    for product in products:
        product.price = product.price * 1.1  # %10 zam
    
    Product.objects.bulk_update(
        products, 
        ['price'], 
        batch_size=100
    )
    
    # Update with F expressions - Veritabanında hesaplama
    Product.objects.filter(
        category_id=1
    ).update(
        price=F('price') * 1.1
    )


# 9. Raw SQL Optimization
def raw_sql_optimization():
    """Ham SQL kullanarak optimizasyon"""
    from django.db import connection
    
    # Complex agregasyon için raw SQL
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                COUNT(DISTINCT o.id) as order_count,
                SUM(oi.quantity * oi.price) as total_revenue,
                AVG(o.total) as avg_order_value
            FROM customers_customer c
            LEFT JOIN orders_order o ON o.customer_id = c.id
            LEFT JOIN orders_orderitem oi ON oi.order_id = o.id
            WHERE c.is_active = true
            GROUP BY c.id, c.name
            HAVING COUNT(DISTINCT o.id) > 0
            ORDER BY total_revenue DESC
            LIMIT 10
        """)
        
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


# 10. Database Index Optimization
"""
Veritabanı index optimizasyonu için migration örneği:

from django.db import migrations

class Migration(migrations.Migration):
    operations = [
        # Tek alan indexi
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['sku'], name='product_sku_idx'),
        ),
        
        # Çoklu alan indexi
        migrations.AddIndex(
            model_name='order',
            index=models.Index(
                fields=['customer', 'status', '-created_at'],
                name='order_customer_status_idx'
            ),
        ),
        
        # Partial index (PostgreSQL)
        migrations.AddIndex(
            model_name='product',
            index=models.Index(
                fields=['category'],
                name='product_active_category_idx',
                condition=Q(is_active=True)
            ),
        ),
    ]
"""


# 11. Query Monitoring
def monitor_query_performance():
    """Query performansını izle"""
    from django.db import connection
    from django.conf import settings
    import time
    
    if not settings.DEBUG:
        return
    
    # Query öncesi zaman
    start_time = time.time()
    initial_queries = len(connection.queries)
    
    # Queries to monitor
    products = Product.objects.select_related(
        'category'
    ).prefetch_related(
        'images',
        'reviews'
    ).filter(
        is_active=True
    )[:100]
    
    # Force evaluation
    list(products)
    
    # Performans metrikleri
    execution_time = time.time() - start_time
    query_count = len(connection.queries) - initial_queries
    
    print(f"Execution time: {execution_time:.4f}s")
    print(f"Query count: {query_count}")
    
    # Her sorguyu analiz et
    for query in connection.queries[initial_queries:]:
        print(f"Time: {query['time']}s")
        print(f"SQL: {query['sql'][:100]}...")
        print("---")


# 12. Lazy Loading Pattern
class LazyLoadingExample:
    """Lazy loading pattern örneği"""
    
    def __init__(self):
        self._expensive_data = None
    
    @property
    def expensive_data(self):
        """Expensive data'yı sadece gerektiğinde yükle"""
        if self._expensive_data is None:
            self._expensive_data = self._load_expensive_data()
        return self._expensive_data
    
    def _load_expensive_data(self):
        """Veritabanından yoğun veri yükleme"""
        from products.models import Product
        
        return Product.objects.select_related(
            'category'
        ).prefetch_related(
            'images',
            'reviews',
            'variants'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            total_sales=Sum('orderitem__quantity')
        ).filter(
            is_active=True
        )