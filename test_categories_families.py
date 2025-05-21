import os
import sys
import django

# Django ayarlarını yükle
sys.path.append('/Users/emreuysal/Documents/Project/VivaCrm v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, Category, ProductFamily
from django.contrib.auth import get_user_model

User = get_user_model()

# Kategoriler oluştur
categories = [
    ('Elektronik', 'Elektronik ürünler'),
    ('Giyim', 'Giyim ve aksesuar ürünleri'),
    ('Kitap', 'Kitap ve kırtasiye ürünleri'),
    ('Oyuncak', 'Oyuncak ve hobi ürünleri'),
    ('Gıda', 'Gıda ve içecek ürünleri'),
]

for name, desc in categories:
    category, created = Category.objects.get_or_create(
        name=name,
        defaults={'description': desc}
    )
    print(f"{'Oluşturuldu' if created else 'Mevcut'}: Kategori - {name}")

# Ürün aileleri oluştur
families = [
    ('Premium Serisi', 'Yüksek kalite premium ürünler'),
    ('Standart Serisi', 'Standart kalite ürünler'),
    ('Ekonomik Serisi', 'Uygun fiyatlı ekonomik ürünler'),
    ('Özel Üretim', 'Sipariş üzerine özel üretim ürünler'),
]

for name, desc in families:
    family, created = ProductFamily.objects.get_or_create(
        name=name,
        defaults={'description': desc}
    )
    print(f"{'Oluşturuldu' if created else 'Mevcut'}: Ürün Ailesi - {name}")

# Mevcut ürünleri güncelleyelim
products = Product.objects.all()
categories_list = list(Category.objects.all())
families_list = list(ProductFamily.objects.all())

import random
for product in products[:10]:  # İlk 10 ürünü güncelleyelim
    product.category = random.choice(categories_list)
    product.family = random.choice(families_list)
    product.save()
    print(f"Güncellendi: {product.name} - Kategori: {product.category.name}, Aile: {product.family.name}")

print(f"\nToplam kategori sayısı: {Category.objects.count()}")
print(f"Toplam ürün ailesi sayısı: {ProductFamily.objects.count()}")
print(f"Toplam ürün sayısı: {Product.objects.count()}")