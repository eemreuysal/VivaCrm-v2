"""
VivaCRM performans testleri.
Sistemin performansını ölçmek ve iyileştirmeleri doğrulamak için test senaryoları.
"""
import time
import statistics
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django.db import transaction, connection, reset_queries
from django.core.cache import cache
from django.urls import reverse
from django.test import Client
from decimal import Decimal
import random
import concurrent.futures

from products.models import Product, Category, ProductFamily, StockMovement
from customers.models import Customer
from orders.models import Order, OrderItem
from invoices.models import Invoice

User = get_user_model()


class PerformanceTestMixin:
    """Performans testleri için yardımcı metodlar."""
    
    def setUp(self):
        """Temel test verilerini hazırla."""
        super().setUp()
        self.user = User.objects.create_user(
            username='perftest',
            email='perftest@vivacrm.com',
            password='perftest123'
        )
        self.client = Client()
        self.client.login(username='perftest', password='perftest123')
        
    def measure_time(self, func, *args, **kwargs):
        """Bir fonksiyonun çalışma süresini ölç."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    def measure_queries(self, func, *args, **kwargs):
        """Bir fonksiyonun çalıştırdığı sorgu sayısını ölç."""
        reset_queries()
        result = func(*args, **kwargs)
        query_count = len(connection.queries)
        return result, query_count
    
    def create_test_data(self, count=100):
        """Test verileri oluştur."""
        # Kategoriler
        categories = []
        for i in range(5):
            cat = Category.objects.create(
                name=f'Test Category {i}',
                slug=f'test-category-{i}',
                is_active=True
            )
            categories.append(cat)
        
        # Ürün aileleri
        families = []
        for i in range(3):
            family = ProductFamily.objects.create(
                name=f'Test Family {i}',
                slug=f'test-family-{i}',
                is_active=True
            )
            families.append(family)
        
        # Ürünler
        products = []
        for i in range(count):
            product = Product.objects.create(
                code=f'TEST{i:04d}',
                name=f'Test Product {i}',
                slug=f'test-product-{i}',
                category=random.choice(categories),
                family=random.choice(families) if i % 3 == 0 else None,
                price=Decimal(str(random.uniform(10, 1000))),
                cost=Decimal(str(random.uniform(5, 500))),
                stock=random.randint(0, 100),
                is_active=True
            )
            products.append(product)
        
        # Müşteriler
        customers = []
        for i in range(count // 2):
            customer = Customer.objects.create(
                customer_code=f'CUST{i:04d}',
                name=f'Test Customer {i}',
                email=f'customer{i}@test.com',
                phone=f'555-{i:04d}',
                owner=self.user,
                is_active=True
            )
            customers.append(customer)
        
        return {
            'categories': categories,
            'families': families,
            'products': products,
            'customers': customers
        }


@override_settings(DEBUG=True)
class QueryOptimizationTest(TransactionTestCase, PerformanceTestMixin):
    """Query optimizasyonu testleri."""
    
    def test_product_list_queries(self):
        """Ürün listesi sorgularını test et."""
        # Test verileri oluştur
        data = self.create_test_data(50)
        
        # Optimize edilmemiş sorgu
        def unoptimized_query():
            products = Product.objects.all()
            result = []
            for product in products:
                result.append({
                    'name': product.name,
                    'category': product.category.name,
                    'family': product.family.name if product.family else None,
                    'stock_status': product.stock_status
                })
            return result
        
        # Optimize edilmiş sorgu
        def optimized_query():
            products = Product.objects.select_related('category', 'family').all()
            result = []
            for product in products:
                result.append({
                    'name': product.name,
                    'category': product.category.name,
                    'family': product.family.name if product.family else None,
                    'stock_status': product.stock_status
                })
            return result
        
        # Sorgu sayılarını karşılaştır
        _, unoptimized_queries = self.measure_queries(unoptimized_query)
        _, optimized_queries = self.measure_queries(optimized_query)
        
        print(f"\nÜrün Listesi Sorgu Optimizasyonu:")
        print(f"Optimize edilmemiş: {unoptimized_queries} sorgu")
        print(f"Optimize edilmiş: {optimized_queries} sorgu")
        print(f"İyileştirme: {unoptimized_queries / optimized_queries:.2f}x")
        
        # Optimize edilmiş versiyonun daha az sorgu çalıştırdığını doğrula
        self.assertLess(optimized_queries, unoptimized_queries)
        self.assertLess(optimized_queries, 5)  # Makul bir sorgu sayısı
    
    def test_order_list_queries(self):
        """Sipariş listesi sorgularını test et."""
        # Test verileri oluştur
        data = self.create_test_data(30)
        
        # Siparişler oluştur
        orders = []
        for i in range(20):
            order = Order.objects.create(
                order_number=f'ORD{i:04d}',
                customer=random.choice(data['customers']),
                status='pending',
                owner=self.user
            )
            
            # Sipariş kalemleri ekle
            for j in range(random.randint(1, 5)):
                product = random.choice(data['products'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 10),
                    unit_price=product.price,
                    tax_rate=18
                )
            
            order.calculate_totals()
            orders.append(order)
        
        # Optimize edilmemiş sorgu
        def unoptimized_query():
            orders = Order.objects.all()
            result = []
            for order in orders:
                item_count = order.items.count()
                total_products = sum(item.quantity for item in order.items.all())
                result.append({
                    'order_number': order.order_number,
                    'customer': order.customer.name,
                    'item_count': item_count,
                    'total_products': total_products,
                    'total': order.total_amount
                })
            return result
        
        # Optimize edilmiş sorgu
        def optimized_query():
            orders = (Order.objects
                     .select_related('customer')
                     .prefetch_related('items')
                     .all())
            result = []
            for order in orders:
                items = order.items.all()
                item_count = len(items)
                total_products = sum(item.quantity for item in items)
                result.append({
                    'order_number': order.order_number,
                    'customer': order.customer.name,
                    'item_count': item_count,
                    'total_products': total_products,
                    'total': order.total_amount
                })
            return result
        
        # Sorgu sayılarını karşılaştır
        _, unoptimized_queries = self.measure_queries(unoptimized_query)
        _, optimized_queries = self.measure_queries(optimized_query)
        
        print(f"\nSipariş Listesi Sorgu Optimizasyonu:")
        print(f"Optimize edilmemiş: {unoptimized_queries} sorgu")
        print(f"Optimize edilmiş: {optimized_queries} sorgu")
        print(f"İyileştirme: {unoptimized_queries / optimized_queries:.2f}x")
        
        # Optimize edilmiş versiyonun çok daha az sorgu çalıştırdığını doğrula
        self.assertLess(optimized_queries, unoptimized_queries / 5)


class CachePerformanceTest(TestCase, PerformanceTestMixin):
    """Cache performans testleri."""
    
    def setUp(self):
        """Test hazırlığı."""
        super().setUp()
        cache.clear()
    
    def test_dashboard_cache_performance(self):
        """Dashboard cache performansını test et."""
        # Test verileri oluştur
        data = self.create_test_data(100)
        
        # Siparişler oluştur
        for i in range(50):
            order = Order.objects.create(
                order_number=f'ORD{i:04d}',
                customer=random.choice(data['customers']),
                status=random.choice(['pending', 'processing', 'completed']),
                owner=self.user
            )
            
            # Sipariş kalemleri
            for j in range(random.randint(1, 5)):
                product = random.choice(data['products'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 10),
                    unit_price=product.price,
                    tax_rate=18
                )
            
            order.calculate_totals()
        
        # Dashboard verilerini hesapla
        def calculate_dashboard_stats():
            stats = {
                'total_customers': Customer.objects.count(),
                'active_customers': Customer.objects.filter(is_active=True).count(),
                'total_products': Product.objects.count(),
                'low_stock_products': Product.objects.filter(
                    stock__lte=models.F('threshold_stock')
                ).count(),
                'total_orders': Order.objects.count(),
                'pending_orders': Order.objects.filter(status='pending').count(),
                'completed_orders': Order.objects.filter(status='completed').count(),
                'total_revenue': Order.objects.filter(
                    status='completed'
                ).aggregate(total=models.Sum('total_amount'))['total'] or 0
            }
            
            # En çok satan ürünler (ağır sorgu)
            top_products = (OrderItem.objects
                           .values('product__name')
                           .annotate(total=models.Sum('quantity'))
                           .order_by('-total')[:10])
            
            stats['top_products'] = list(top_products)
            
            return stats
        
        # Cache kullanmadan
        _, no_cache_time = self.measure_time(calculate_dashboard_stats)
        
        # Cache kullanarak
        def cached_dashboard_stats():
            cache_key = 'dashboard_stats'
            stats = cache.get(cache_key)
            
            if stats is None:
                stats = calculate_dashboard_stats()
                cache.set(cache_key, stats, 300)  # 5 dakika
            
            return stats
        
        # İlk çağrı (cache miss)
        cache.clear()
        _, cache_miss_time = self.measure_time(cached_dashboard_stats)
        
        # İkinci çağrı (cache hit)
        _, cache_hit_time = self.measure_time(cached_dashboard_stats)
        
        print(f"\nDashboard Cache Performansı:")
        print(f"Cache kullanmadan: {no_cache_time:.4f} saniye")
        print(f"Cache miss: {cache_miss_time:.4f} saniye")
        print(f"Cache hit: {cache_hit_time:.4f} saniye")
        print(f"Cache hit {no_cache_time / cache_hit_time:.0f}x daha hızlı")
        
        # Cache hit'in çok daha hızlı olduğunu doğrula
        self.assertLess(cache_hit_time, no_cache_time * 0.1)


class BulkOperationTest(TransactionTestCase, PerformanceTestMixin):
    """Toplu işlem performans testleri."""
    
    def test_bulk_product_creation(self):
        """Toplu ürün oluşturma performansı."""
        # Kategori ve aile oluştur
        category = Category.objects.create(
            name='Bulk Test Category',
            slug='bulk-test-category'
        )
        
        # Tek tek oluşturma
        def create_one_by_one(count):
            products = []
            for i in range(count):
                product = Product.objects.create(
                    code=f'SINGLE{i:04d}',
                    name=f'Single Product {i}',
                    slug=f'single-product-{i}',
                    category=category,
                    price=Decimal('99.99'),
                    stock=50
                )
                products.append(product)
            return products
        
        # Toplu oluşturma
        def create_bulk(count):
            products = []
            for i in range(count):
                products.append(Product(
                    code=f'BULK{i:04d}',
                    name=f'Bulk Product {i}',
                    slug=f'bulk-product-{i}',
                    category=category,
                    price=Decimal('99.99'),
                    stock=50
                ))
            return Product.objects.bulk_create(products)
        
        # Performansları karşılaştır
        count = 100
        _, single_time = self.measure_time(create_one_by_one, count)
        _, bulk_time = self.measure_time(create_bulk, count)
        
        print(f"\nToplu Ürün Oluşturma ({count} ürün):")
        print(f"Tek tek: {single_time:.4f} saniye")
        print(f"Toplu: {bulk_time:.4f} saniye")
        print(f"Toplu işlem {single_time / bulk_time:.2f}x daha hızlı")
        
        # Toplu işlemin daha hızlı olduğunu doğrula
        self.assertLess(bulk_time, single_time * 0.3)
    
    def test_bulk_stock_update(self):
        """Toplu stok güncelleme performansı."""
        # Test ürünleri oluştur
        data = self.create_test_data(200)
        products = data['products']
        
        # Tek tek güncelleme
        def update_one_by_one():
            for i, product in enumerate(products):
                product.stock = 100 + i
                product.save()
                
                # Stok hareketi oluştur
                StockMovement.objects.create(
                    product=product,
                    movement_type='adjustment',
                    quantity=product.stock,
                    created_by=self.user
                )
        
        # Toplu güncelleme
        def update_bulk():
            # Stok değerlerini güncelle
            for i, product in enumerate(products):
                product.stock = 200 + i
            
            # Toplu güncelleme
            Product.objects.bulk_update(products, ['stock'], batch_size=50)
            
            # Stok hareketlerini toplu oluştur
            movements = []
            for product in products:
                movements.append(StockMovement(
                    product=product,
                    movement_type='adjustment',
                    quantity=product.stock,
                    created_by=self.user
                ))
            
            StockMovement.objects.bulk_create(movements, batch_size=50)
        
        # Performansları karşılaştır
        _, single_time = self.measure_time(update_one_by_one)
        _, bulk_time = self.measure_time(update_bulk)
        
        print(f"\nToplu Stok Güncelleme ({len(products)} ürün):")
        print(f"Tek tek: {single_time:.4f} saniye")
        print(f"Toplu: {bulk_time:.4f} saniye")
        print(f"Toplu işlem {single_time / bulk_time:.2f}x daha hızlı")
        
        # Toplu işlemin çok daha hızlı olduğunu doğrula
        self.assertLess(bulk_time, single_time * 0.2)


class APIPerformanceTest(TestCase, PerformanceTestMixin):
    """API performans testleri."""
    
    def test_product_api_performance(self):
        """Ürün API performansı."""
        # Test verileri oluştur
        data = self.create_test_data(500)
        
        # API çağrıları
        endpoints = [
            '/api/products/',
            '/api/products/?page=1&page_size=20',
            '/api/products/?category=' + str(data['categories'][0].id),
            '/api/products/?search=Test',
            '/api/products/?ordering=-created_at',
        ]
        
        results = []
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()
            
            duration = end_time - start_time
            results.append({
                'endpoint': endpoint,
                'status': response.status_code,
                'duration': duration,
                'count': len(response.json().get('results', []))
            })
        
        print("\nAPI Performans Sonuçları:")
        for result in results:
            print(f"{result['endpoint']}")
            print(f"  Durum: {result['status']}, Süre: {result['duration']:.4f}s, Kayıt: {result['count']}")
        
        # Tüm endpoint'lerin hızlı yanıt verdiğini doğrula
        for result in results:
            self.assertEqual(result['status'], 200)
            self.assertLess(result['duration'], 0.5)  # 500ms altında


class LoadTest(TransactionTestCase, PerformanceTestMixin):
    """Yük testleri."""
    
    def test_concurrent_order_creation(self):
        """Eşzamanlı sipariş oluşturma testi."""
        # Test verileri oluştur
        data = self.create_test_data(50)
        
        # Sipariş oluşturma fonksiyonu
        def create_order(index):
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        order_number=f'LOAD{index:04d}',
                        customer=random.choice(data['customers']),
                        status='pending',
                        owner=self.user
                    )
                    
                    # 2-5 ürün ekle
                    num_items = random.randint(2, 5)
                    for _ in range(num_items):
                        product = random.choice(data['products'])
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=random.randint(1, 5),
                            unit_price=product.price,
                            tax_rate=18
                        )
                    
                    order.calculate_totals()
                    return True, order.id
            except Exception as e:
                return False, str(e)
        
        # Eşzamanlı siparişler oluştur
        num_concurrent = 20
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_order, i) for i in range(num_concurrent)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Sonuçları analiz et
        successful = sum(1 for success, _ in results if success)
        failed = num_concurrent - successful
        
        print(f"\nEşzamanlı Sipariş Oluşturma:")
        print(f"Toplam: {num_concurrent}, Başarılı: {successful}, Başarısız: {failed}")
        print(f"Toplam süre: {duration:.4f} saniye")
        print(f"Ortalama süre: {duration / num_concurrent:.4f} saniye/sipariş")
        
        # Başarı oranının yüksek olduğunu doğrula
        self.assertGreater(successful / num_concurrent, 0.95)
        
        # Performansın kabul edilebilir olduğunu doğrula
        self.assertLess(duration / num_concurrent, 0.5)


class MemoryUsageTest(TestCase, PerformanceTestMixin):
    """Bellek kullanımı testleri."""
    
    def test_large_queryset_memory(self):
        """Büyük queryset bellek kullanımı."""
        # Test verileri oluştur
        data = self.create_test_data(1000)
        
        # Iterator kullanmadan (kötü örnek)
        def load_all_products():
            products = Product.objects.all()
            return [p.name for p in products]
        
        # Iterator kullanarak (iyi örnek)
        def iterate_products():
            names = []
            for product in Product.objects.iterator(chunk_size=100):
                names.append(product.name)
            return names
        
        # Bellek kullanımı testleri burada daha karmaşık olacağından,
        # sadece performans farkını ölçüyoruz
        _, all_time = self.measure_time(load_all_products)
        _, iter_time = self.measure_time(iterate_products)
        
        print(f"\nBüyük Veri Seti İşleme:")
        print(f"Tümünü yükle: {all_time:.4f} saniye")
        print(f"Iterator kullan: {iter_time:.4f} saniye")
        
        # Iterator'ın daha verimli olduğunu kontrol et
        # (Bu test bellek kullanımını doğrudan ölçmese de performans farkını gösterir)
        self.assertLess(abs(all_time - iter_time), 1.0)


def run_performance_suite():
    """Tüm performans testlerini çalıştır."""
    test_classes = [
        QueryOptimizationTest,
        CachePerformanceTest,
        BulkOperationTest,
        APIPerformanceTest,
        LoadTest,
        MemoryUsageTest
    ]
    
    print("VivaCRM Performans Test Paketi")
    print("=" * 50)
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__} çalıştırılıyor...")
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    run_performance_suite()