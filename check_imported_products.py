#!/usr/bin/env python3
"""
Check the imported products in the database.
"""

import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, Category, ProductFamily

def check_imported_products():
    """Check the imported products."""
    
    print("Checking imported products...")
    print("=" * 60)
    
    # Check totals
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_families = ProductFamily.objects.count()
    
    print(f"\nDatabase totals:")
    print(f"  Products: {total_products}")
    print(f"  Categories: {total_categories}")
    print(f"  Product Families: {total_families}")
    
    # Check first few products
    print("\nFirst 5 products:")
    for product in Product.objects.all()[:5]:
        print(f"\n  Product: {product.name[:60]}...")
        print(f"    SKU: {product.sku}")
        print(f"    Code: {product.code}")
        print(f"    Price: {product.price}")
        print(f"    Category: {product.category.name if product.category else 'None'}")
        print(f"    Family: {product.family.name[:50] if product.family else 'None'}...")
    
    # Check categories
    print("\nAll categories:")
    for category in Category.objects.all():
        product_count = category.products.count()
        print(f"  - {category.name} ({product_count} products)")
    
    # Check families
    print("\nAll product families:")
    for family in ProductFamily.objects.all():
        product_count = family.products.count()
        print(f"  - {family.name[:60]}... ({product_count} products)")
    
    # Check for SKUs with newlines (should be none)
    products_with_newline_sku = Product.objects.filter(sku__contains='\n')
    print(f"\nProducts with newline in SKU: {products_with_newline_sku.count()}")
    
    print("\n" + "=" * 60)
    print("Check complete!")


if __name__ == '__main__':
    check_imported_products()