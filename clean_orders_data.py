#!/usr/bin/env python
"""Clean orders data before import."""
import os
import sys
import django

sys.path.append('/Users/emreuysal/Documents/Project/VivaCrm v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order, OrderItem
from products.models import Product

print("Cleaning orders data...")

# Delete all order items
order_items_deleted = OrderItem.objects.all().delete()
print(f"Deleted {order_items_deleted[0]} order items")

# Delete all orders
orders_deleted = Order.objects.all().delete()
print(f"Deleted {orders_deleted[0]} orders")

# Delete products created from import
import_products = Product.objects.filter(description__contains="Sipariş import'tan oluşturuldu")
products_deleted = import_products.delete()
print(f"Deleted {products_deleted[0]} import products")

print("\nCleanup completed. Ready for import.")