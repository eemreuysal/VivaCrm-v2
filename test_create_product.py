import os
import sys
import django

# Django ayarlarını yükle
sys.path.append('/Users/emreuysal/Documents/Project/VivaCrm v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

# Test kategorisi oluştur (varsa kullan)
category, created = Category.objects.get_or_create(
    name="Test Kategorisi",
    defaults={'description': 'Test amaçlı kategori'}
)

# Test ürünleri oluştur
for i in range(1, 11):
    product, created = Product.objects.get_or_create(
        code=f"TEST{i:03d}",
        defaults={
            'name': f'Test Ürün {i}',
            'description': f'Test ürünü {i} açıklaması',
            'category': category,
            'price': float(i * 100),
            'stock': i * 10,
            'is_active': True,
            'is_physical': True,
            'status': 'available'
        }
    )
    if created:
        print(f"Oluşturuldu: {product.name}")
    else:
        print(f"Mevcut: {product.name}")

print(f"\nToplam ürün sayısı: {Product.objects.count()}")