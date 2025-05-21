#!/usr/bin/env python
"""
Test script to verify the optimized Excel import performance
"""
import os
import django
import time
import logging
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product, Category
from core.excel_corrections import AutoCorrector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()


def test_category_lookup_optimization():
    """Test category lookup optimization"""
    logger.info("Testing category lookup optimization...")
    
    # Create test categories
    categories = []
    for i in range(100):
        category = Category.objects.create(
            name=f"Test Category {i}",
            slug=f"test-category-{i}"
        )
        categories.append(category)
    
    # Test old method (N+1 queries)
    start_time = time.time()
    queries_before = len(connection.queries)
    
    for i in range(50):
        category_name = f"Some Category {i}"
        exists = Category.objects.filter(name__iexact=category_name).exists()
    
    old_method_time = time.time() - start_time
    old_method_queries = len(connection.queries) - queries_before
    
    logger.info(f"Old method: {old_method_time:.4f}s, {old_method_queries} queries")
    
    # Test new method (cached lookups)
    start_time = time.time()
    queries_before = len(connection.queries)
    
    # Cache categories
    existing_categories = set(Category.objects.values_list('name', flat=True))
    existing_categories_lower = {cat.lower() for cat in existing_categories}
    
    for i in range(50):
        category_name = f"Some Category {i}"
        exists = category_name.lower() in existing_categories_lower
    
    new_method_time = time.time() - start_time
    new_method_queries = len(connection.queries) - queries_before
    
    logger.info(f"New method: {new_method_time:.4f}s, {new_method_queries} queries")
    logger.info(f"Performance improvement: {old_method_time/new_method_time:.2f}x faster")
    logger.info(f"Query reduction: {old_method_queries - new_method_queries} fewer queries")
    
    # Cleanup
    Category.objects.filter(name__startswith="Test Category").delete()


def test_autocorrector_optimization():
    """Test AutoCorrector optimization"""
    logger.info("\nTesting AutoCorrector optimization...")
    
    # Create test categories for similarity matching
    categories = []
    for i in range(50):
        category = Category.objects.create(
            name=f"Product Category {i}",
            slug=f"product-category-{i}"
        )
        categories.append(category)
    
    # Test without caching
    start_time = time.time()
    queries_before = len(connection.queries)
    
    for i in range(20):
        corrector = AutoCorrector()  # Creating new instance each time
        category_name = f"Product Categry {i}"  # Intentional typo
        result = corrector.find_similar_category(category_name)
    
    no_cache_time = time.time() - start_time
    no_cache_queries = len(connection.queries) - queries_before
    
    logger.info(f"Without caching: {no_cache_time:.4f}s, {no_cache_queries} queries")
    
    # Test with caching (reusing instance)
    start_time = time.time()
    queries_before = len(connection.queries)
    
    corrector = AutoCorrector()  # Single instance
    for i in range(20):
        category_name = f"Product Categry {i}"  # Intentional typo
        result = corrector.find_similar_category(category_name)
    
    with_cache_time = time.time() - start_time
    with_cache_queries = len(connection.queries) - queries_before
    
    logger.info(f"With caching: {with_cache_time:.4f}s, {with_cache_queries} queries")
    logger.info(f"Performance improvement: {no_cache_time/with_cache_time:.2f}x faster")
    logger.info(f"Query reduction: {no_cache_queries - with_cache_queries} fewer queries")
    
    # Cleanup
    Category.objects.filter(name__startswith="Product Category").delete()


if __name__ == "__main__":
    logger.info("Starting optimization tests...")
    
    # Ensure we have a test user
    user, _ = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com', 'is_staff': True}
    )
    
    test_category_lookup_optimization()
    test_autocorrector_optimization()
    
    logger.info("\nOptimization tests completed.")