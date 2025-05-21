#!/usr/bin/env python
"""
Test that categories exist in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Category

# Test specific categories that appear in the error screenshot
test_categories = [
    "Muslin Towel",
    "Waffle Robe Kimono",
    "Pom Pom Towel", 
    "Beach Towel",
    "Terry Towel",
    "Organic Bedwear",
    "Solid Color Bamboo Towel",
    "Scarf Beach Towel"
]

print("Checking if categories exist:")
print("-" * 50)

for category_name in test_categories:
    exists = Category.objects.filter(name__iexact=category_name).exists()
    count = Category.objects.filter(name__iexact=category_name).count()
    print(f"Category: {category_name:30} - Exists: {exists:5} - Count: {count}")

print("\nAll categories in database:")
print("-" * 50)

for category in Category.objects.all().order_by('name'):
    print(f"ID: {category.id:5} - Name: {category.name:30} - Slug: {category.slug}")

print(f"\nTotal categories: {Category.objects.count()}")