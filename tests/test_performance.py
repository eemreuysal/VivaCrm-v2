"""
VivaCRM v2 Performance Test Suite

Bu dosya, performans iyileştirmelerini test etmek için kullanılacak test senaryolarını içerir.
"""
import time
import pytest
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, reset_queries
from django.conf import settings
from django.utils import timezone
from unittest.mock import patch, MagicMock
import json
import locust
from locust import HttpUser, task, between
from faker import Faker

User = get_user_model()
fake = Faker()


# 1. Database Performance Tests
class DatabasePerformanceTest(TransactionTestCase):
    """Veritabanı performans testleri"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Test verilerini oluştur"""
        from products.models import Product, Category
        from customers.models import Customer
        from orders.models import Order
        
        # Categories
        categories = []
        for i in range(10):
            category = Category.objects.create(
                name=f"Category {i}",
                slug=f"category-{i}"
            )
            categories.append(category)
        
        # Products
        products = []
        for i in range(1000):
            product = Product.objects.create(
                name=f"Product {i}",
                sku=f"SKU{i:04d}",
                category=categories[i % 10],
                price=fake.random_int(10, 1000),
                stock=fake.random_int(0, 100)
            )
            products.append(product)
        
        # Customers
        customers = []
        for i in range(100):
            customer = Customer.objects.create(
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number(),
                created_by=self.user
            )
            customers.append(customer)
        
        # Orders
        for i in range(500):
            order = Order.objects.create(
                customer=customers[i % 100],
                total=fake.random_int(100, 5000),
                status='pending',
                created_by=self.user
            )
    
    def test_n_plus_1_queries(self):
        """N+1 query problemini test et"""
        from core.query_optimizer import detect_n_plus_1
        from orders.models import Order
        
        # Without optimization
        reset_queries()
        orders = Order.objects.all()[:10]
        
        # Access related fields - this should cause N+1
        for order in orders:
            _ = order.customer.name
            _ = order.created_by.username
        
        unoptimized_queries = len(connection.queries)
        
        # With optimization
        reset_queries()
        orders = Order.objects.select_related(
            'customer', 'created_by'
        )[:10]
        
        # Access related fields - no N+1
        for order in orders:
            _ = order.customer.name
            _ = order.created_by.username
        
        optimized_queries = len(connection.queries)
        
        # Assert optimization worked
        self.assertLess(optimized_queries, unoptimized_queries)
        self.assertEqual(optimized_queries, 1)  # Should be single query
    
    def test_query_performance(self):
        """Query performansını test et"""
        from orders.models import Order
        from django.db.models import Count, Sum, Avg
        
        # Complex aggregation query
        start_time = time.time()
        
        stats = Order.objects.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total'),
            avg_order_value=Avg('total')
        )
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete in reasonable time
        self.assertLess(query_time, 0.1)  # 100ms
        
        # Check results
        self.assertGreater(stats['total_orders'], 0)
        self.assertIsNotNone(stats['total_revenue'])
        self.assertIsNotNone(stats['avg_order_value'])
    
    def test_bulk_operations(self):
        """Bulk operations performansını test et"""
        from products.models import Product
        from core.db_optimizations import BatchOperations
        
        # Create 1000 products
        products = []
        for i in range(1000):
            products.append(Product(
                name=f"Bulk Product {i}",
                sku=f"BULK{i:04d}",
                price=100
            ))
        
        # Test bulk create
        start_time = time.time()
        BatchOperations.bulk_create_with_batch(
            Product, products, batch_size=100
        )
        end_time = time.time()
        
        bulk_create_time = end_time - start_time
        
        # Should be fast
        self.assertLess(bulk_create_time, 1.0)  # Less than 1 second
        
        # Verify created
        self.assertEqual(
            Product.objects.filter(name__startswith="Bulk Product").count(),
            1000
        )


# 2. Cache Performance Tests
class CachePerformanceTest(TestCase):
    """Cache performans testleri"""
    
    def setUp(self):
        cache.clear()
    
    def test_cache_hit_performance(self):
        """Cache hit performansını test et"""
        from core.cache import cache_function
        
        # Create cached function
        @cache_function(timeout=60)
        def expensive_calculation(n):
            time.sleep(0.1)  # Simulate expensive operation
            return n * n
        
        # First call - cache miss
        start_time = time.time()
        result1 = expensive_calculation(42)
        miss_time = time.time() - start_time
        
        # Second call - cache hit
        start_time = time.time()
        result2 = expensive_calculation(42)
        hit_time = time.time() - start_time
        
        # Assert cache hit is much faster
        self.assertEqual(result1, result2)
        self.assertLess(hit_time, miss_time / 10)  # 10x faster
    
    def test_cache_invalidation(self):
        """Cache invalidation performansını test et"""
        from core.cache import invalidate_cache_prefix
        
        # Set multiple cache entries
        for i in range(100):
            cache.set(f"test:item:{i}", i, timeout=60)
        
        # Verify all cached
        for i in range(100):
            self.assertEqual(cache.get(f"test:item:{i}"), i)
        
        # Invalidate by prefix
        start_time = time.time()
        invalidate_cache_prefix("test:item:")
        invalidation_time = time.time() - start_time
        
        # Should be fast
        self.assertLess(invalidation_time, 0.1)  # 100ms
        
        # Verify all invalidated
        for i in range(100):
            self.assertIsNone(cache.get(f"test:item:{i}"))
    
    def test_cache_stampede_prevention(self):
        """Cache stampede prevention test"""
        from threading import Thread
        from core.cache import cache_function
        
        call_count = 0
        
        @cache_function(timeout=60)
        def expensive_operation():
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)
            return call_count
        
        # Create multiple threads requesting same cache
        threads = []
        results = []
        
        def worker():
            result = expensive_operation()
            results.append(result)
        
        # Start 10 threads simultaneously
        for _ in range(10):
            thread = Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should only be called once despite multiple threads
        self.assertEqual(call_count, 1)
        self.assertEqual(len(set(results)), 1)  # All results same


# 3. API Performance Tests
class APIPerformanceTest(TestCase):
    """API performans testleri"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.login(username='testuser', password='testpass')
    
    def test_api_response_time(self):
        """API response time test"""
        # Create test data
        from products.models import Product, Category
        
        category = Category.objects.create(name="Test", slug="test")
        for i in range(100):
            Product.objects.create(
                name=f"Product {i}",
                category=category,
                price=100
            )
        
        # Test API performance
        start_time = time.time()
        response = self.client.get('/api/products/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should be fast
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 0.2)  # 200ms
        
        # Check response has proper headers
        self.assertIn('X-Response-Time', response.headers)
        self.assertIn('X-Query-Count', response.headers)
    
    def test_api_pagination_performance(self):
        """API pagination performansını test et"""
        # Create many products
        from products.models import Product, Category
        
        category = Category.objects.create(name="Test", slug="test")
        Product.objects.bulk_create([
            Product(
                name=f"Product {i}",
                category=category,
                price=100
            )
            for i in range(1000)
        ])
        
        # Test different page sizes
        page_sizes = [20, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = self.client.get(
                f'/api/products/?page_size={page_size}'
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should scale reasonably
            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 0.1 * (page_size / 20))
    
    def test_api_field_selection(self):
        """API field selection performansını test et"""
        from products.models import Product, Category
        
        category = Category.objects.create(name="Test", slug="test")
        Product.objects.create(name="Test Product", category=category, price=100)
        
        # Full response
        start_time = time.time()
        response_full = self.client.get('/api/products/')
        full_time = time.time() - start_time
        
        # Limited fields
        start_time = time.time()
        response_limited = self.client.get('/api/products/?fields=id,name')
        limited_time = time.time() - start_time
        
        # Limited fields should be faster
        self.assertLess(limited_time, full_time)
        
        # Check response size difference
        self.assertLess(
            len(response_limited.content),
            len(response_full.content)
        )


# 4. Celery Performance Tests
class CeleryPerformanceTest(TestCase):
    """Celery performans testleri"""
    
    @patch('celery.current_app.send_task')
    def test_task_execution_time(self, mock_send_task):
        """Task execution time test"""
        from core.celery_optimizations import process_large_dataset
        
        # Mock task execution
        mock_send_task.return_value.get.return_value = {'processed': 1000}
        
        # Execute task
        start_time = time.time()
        result = process_large_dataset.delay('dataset-1', chunk_size=100)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should be fast to queue
        self.assertLess(execution_time, 0.01)  # 10ms
    
    def test_task_batching(self):
        """Task batching performansını test et"""
        from core.celery_optimizations import BatchProcessor
        
        processor = BatchProcessor(batch_size=100)
        
        # Add items to batch
        start_time = time.time()
        for i in range(1000):
            processor.add_to_batch('test_batch', {'id': i})
        end_time = time.time()
        
        add_time = end_time - start_time
        
        # Should be fast
        self.assertLess(add_time, 0.1)  # 100ms for 1000 items
        
        # Process batch
        processed_count = 0
        
        def process_items(items):
            nonlocal processed_count
            processed_count += len(items)
            return processed_count
        
        while True:
            result = processor.process_batch('test_batch', process_items)
            if result is None:
                break
        
        # Should process all items
        self.assertEqual(processed_count, 1000)


# 5. Load Tests with Locust
class VivaCRMUser(HttpUser):
    """Locust user for load testing"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login user"""
        self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass'
        })
    
    @task(3)
    def view_products(self):
        """View products list"""
        self.client.get('/api/products/')
    
    @task(2)
    def view_product_detail(self):
        """View product detail"""
        product_id = fake.random_int(1, 100)
        self.client.get(f'/api/products/{product_id}/')
    
    @task(1)
    def create_order(self):
        """Create order"""
        self.client.post('/api/orders/', json={
            'customer_id': fake.random_int(1, 100),
            'items': [
                {
                    'product_id': fake.random_int(1, 100),
                    'quantity': fake.random_int(1, 5)
                }
            ]
        })
    
    @task(2)
    def view_dashboard(self):
        """View dashboard"""
        self.client.get('/api/dashboard/stats/')


# 6. Stress Tests
class StressTest(TestCase):
    """Stress testing"""
    
    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        from concurrent.futures import ThreadPoolExecutor
        from products.models import Product, Category
        
        # Create test data
        category = Category.objects.create(name="Test", slug="test")
        Product.objects.create(name="Test Product", category=category, price=100)
        
        # Login
        self.client.login(username='testuser', password='testpass')
        
        def make_request():
            return self.client.get('/api/products/')
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in futures]
            end_time = time.time()
        
        total_time = end_time - start_time
        
        # All requests should succeed
        for result in results:
            self.assertEqual(result.status_code, 200)
        
        # Should handle concurrent requests efficiently
        self.assertLess(total_time, 5.0)  # 100 requests in 5 seconds
    
    def test_memory_usage(self):
        """Test memory usage under load"""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        from products.models import Product, Category
        
        category = Category.objects.create(name="Test", slug="test")
        
        # Bulk create products
        products = []
        for i in range(10000):
            products.append(Product(
                name=f"Product {i}",
                category=category,
                price=100
            ))
        
        Product.objects.bulk_create(products, batch_size=1000)
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100)  # Less than 100MB increase


# 7. Benchmark Tests
class BenchmarkTest(TestCase):
    """Performance benchmark tests"""
    
    def test_response_time_benchmarks(self):
        """Test response time benchmarks"""
        benchmarks = {
            '/api/products/': 200,  # 200ms
            '/api/orders/': 300,    # 300ms
            '/api/dashboard/stats/': 500,  # 500ms
        }
        
        self.client.login(username='testuser', password='testpass')
        
        for endpoint, max_time_ms in benchmarks.items():
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(
                response_time_ms, 
                max_time_ms,
                f"{endpoint} took {response_time_ms}ms, max is {max_time_ms}ms"
            )
    
    def test_database_query_benchmarks(self):
        """Test database query benchmarks"""
        from products.models import Product
        from orders.models import Order
        from customers.models import Customer
        
        # Simple queries should be fast
        queries = [
            (Product.objects.count(), 10),  # 10ms
            (Order.objects.filter(status='pending').count(), 20),  # 20ms
            (Customer.objects.filter(is_active=True).count(), 20),  # 20ms
        ]
        
        for query, max_time_ms in queries:
            start_time = time.time()
            result = query
            end_time = time.time()
            
            query_time_ms = (end_time - start_time) * 1000
            
            self.assertLess(
                query_time_ms,
                max_time_ms,
                f"Query took {query_time_ms}ms, max is {max_time_ms}ms"
            )