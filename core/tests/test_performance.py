from django.test import TestCase, TransactionTestCase, tag
from django.urls import reverse
from django.db import connection, reset_queries
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.conf import settings
import time
import unittest
from decimal import Decimal

from core.tests.test_utils import TestDataGenerator
from core.query_optimizer import QueryCountMiddleware, detect_n_plus_1
from customers.models import Customer
from products.models import Product
from orders.models import Order

User = get_user_model()


@tag('performance')
class QueryCountTest(TestCase):
    """Test cases for measuring query counts."""
    
    def setUp(self):
        """Set up test data."""
        # Save original DEBUG setting and temporarily enable it for tests
        self.original_debug = settings.DEBUG
        settings.DEBUG = True
        
        # Create test user
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='perfpassword',
            is_staff=True
        )
        
        # Set up client
        self.client = Client()
        self.client.force_login(self.user)
        
        # Create test data
        self.create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore original DEBUG setting
        settings.DEBUG = self.original_debug
    
    def create_test_data(self):
        """Create test data for performance testing."""
        # Create customers
        for i in range(10):
            customer = TestDataGenerator.create_customer(
                user=self.user,
                name=f"Performance Customer {i}"
            )
            
            # Create addresses for each customer
            TestDataGenerator.create_address(customer, 'billing', True)
            TestDataGenerator.create_address(customer, 'shipping', True)
            
            # Create corporate customers with contacts
            if i % 3 == 0:
                corporate = TestDataGenerator.create_customer(
                    user=self.user,
                    customer_type='corporate',
                    name=f"Corp Customer {i}"
                )
                TestDataGenerator.create_contact(corporate, True)
                TestDataGenerator.create_contact(corporate, False)
        
        # Create products
        category1 = TestDataGenerator.create_category("Performance Category 1")
        category2 = TestDataGenerator.create_category("Performance Category 2")
        
        for i in range(20):
            TestDataGenerator.create_product(
                category=category1 if i % 2 == 0 else category2,
                price=Decimal(f"{100 + i}.99"),
                stock=50
            )
        
        # Create orders with items
        for i in range(5):
            customer = Customer.objects.all()[i]
            order = TestDataGenerator.create_order(customer=customer)
            TestDataGenerator.add_order_items(order, num_items=3)
    
    def count_queries(self, reset=True):
        """Count the number of executed queries."""
        count = len(connection.queries)
        if reset:
            reset_queries()
        return count
    
    def test_customer_list_query_count(self):
        """Test query count for customer list view."""
        reset_queries()
        
        # Get the customer list
        response = self.client.get(reverse('api:customer-list'))
        
        # Count queries
        query_count = self.count_queries()
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Log query count
        print(f"Customer list query count: {query_count}")
        
        # Assert query count is below threshold
        # This is a baseline test - the actual threshold should be determined
        # based on the expected behavior of your views
        self.assertLess(query_count, 10)
    
    def test_order_detail_query_count(self):
        """Test query count for order detail view."""
        # Get an order for testing
        order = Order.objects.first()
        
        reset_queries()
        
        # Get the order detail
        response = self.client.get(reverse('api:order-detail', args=[order.id]))
        
        # Count queries
        query_count = self.count_queries()
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Log query count
        print(f"Order detail query count: {query_count}")
        
        # Assert query count is below threshold
        self.assertLess(query_count, 15)
    
    def test_n_plus_1_detection(self):
        """Test detection of N+1 query problems."""
        # Test on the Order queryset
        order_queryset = Order.objects.all()
        
        # Run detection
        detection_result = detect_n_plus_1(order_queryset)
        
        # Log results
        print(f"N+1 detection for Orders: {detection_result}")
        
        # Assert no N+1 problem for orders (after optimization)
        # Note: This might fail if the optimizations aren't applied
        self.assertFalse(detection_result['has_n_plus_1'])


@tag('performance')
class ResponseTimeTest(TransactionTestCase):
    """Test cases for measuring response times."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='timeuser',
            email='time@example.com',
            password='timepassword',
            is_staff=True
        )
        
        # Set up client
        self.client = Client()
        self.client.force_login(self.user)
        
        # Create test data
        self.create_test_data()
    
    def create_test_data(self):
        """Create test data for timing tests."""
        # Create a large dataset
        for i in range(50):
            customer = TestDataGenerator.create_customer(
                user=self.user,
                name=f"Timing Customer {i}"
            )
            
            TestDataGenerator.create_address(customer, 'billing', True)
            
            if i % 5 == 0:
                order = TestDataGenerator.create_order(customer=customer)
                TestDataGenerator.add_order_items(order, num_items=3)
    
    def measure_response_time(self, url):
        """Measure the response time for a URL."""
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Check response was successful
        self.assertEqual(response.status_code, 200)
        
        return duration
    
    def test_dashboard_response_time(self):
        """Test response time for the dashboard view."""
        # Skip in CI environments where timing can be inconsistent
        if 'CI' in settings.DATABASES:
            raise unittest.SkipTest("Skipping timing test in CI environment")
        
        url = reverse('dashboard:home')
        duration = self.measure_response_time(url)
        
        # Log response time
        print(f"Dashboard response time: {duration:.4f} seconds")
        
        # Assert response time is below threshold
        # The threshold might need adjustment depending on the environment
        self.assertLess(duration, 0.5)
    
    def test_customer_list_response_time(self):
        """Test response time for the customer list API."""
        # Skip in CI environments
        if 'CI' in settings.DATABASES:
            raise unittest.SkipTest("Skipping timing test in CI environment")
        
        url = reverse('api:customer-list')
        duration = self.measure_response_time(url)
        
        # Log response time
        print(f"Customer list response time: {duration:.4f} seconds")
        
        # Assert response time is below threshold
        self.assertLess(duration, 0.3)


@tag('performance')
class PaginationPerformanceTest(TestCase):
    """Test pagination performance with large datasets."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='pageuser',
            email='page@example.com',
            password='pagepassword',
            is_staff=True
        )
        
        # Set up client
        self.client = Client()
        self.client.force_login(self.user)
        
        # Create test data - larger dataset
        self.create_test_data()
    
    def create_test_data(self):
        """Create a larger dataset for pagination testing."""
        # Create products (larger set)
        category = TestDataGenerator.create_category("Pagination Category")
        
        for i in range(100):  # 100 products
            TestDataGenerator.create_product(
                category=category,
                price=Decimal(f"{100 + (i % 20)}.99"),
                stock=50
            )
    
    def test_product_list_pagination(self):
        """Test that pagination works efficiently with large datasets."""
        # Save original DEBUG setting and temporarily enable it for tests
        original_debug = settings.DEBUG
        settings.DEBUG = True
        
        # First page
        reset_queries()
        response1 = self.client.get(reverse('api:product-list'))
        query_count1 = len(connection.queries)
        
        # Second page
        reset_queries()
        response2 = self.client.get(reverse('api:product-list') + '?page=2')
        query_count2 = len(connection.queries)
        
        # Restore DEBUG setting
        settings.DEBUG = original_debug
        
        # Check responses
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Log query counts
        print(f"Product list page 1 query count: {query_count1}")
        print(f"Product list page 2 query count: {query_count2}")
        
        # Verify pagination works (results should be paginated)
        self.assertTrue('next' in response1.data)
        self.assertTrue('previous' in response2.data)
        
        # Query counts should be similar for both pages
        # A large difference might indicate inefficient pagination
        self.assertLess(abs(query_count1 - query_count2), 3)
        
        # Each page should have a reasonable query count
        self.assertLess(query_count1, 10)
        self.assertLess(query_count2, 10)