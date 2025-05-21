#!/usr/bin/env python
"""
Recreate the missing categories that were shown in the error screenshot
"""
import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Category

# Categories from the error screenshot
categories_to_create = [
    "Muslin Towel",
    "Waffle Robe Kimono",
    "Pom Pom Towel", 
    "Beach Towel",
    "Terry Towel",
    "Organic Bedwear",
    "Solid Color Bamboo Towel",
    "Scarf Beach Towel",
    "Waffle Pique Towel",
    "Bamboo Towel",
    "Combed Cotton Towel",
    "Gauffre Bamboo Towel"
]

print("Creating missing categories:")
print("-" * 50)

created_count = 0
for category_name in categories_to_create:
    category, created = Category.objects.get_or_create(
        name=category_name,
        defaults={'slug': slugify(category_name)}
    )
    status = "Created" if created else "Already exists"
    print(f"Category: {category_name:30} - {status}")
    if created:
        created_count += 1

print(f"\nTotal new categories created: {created_count}")
print(f"Total categories now: {Category.objects.count()}")