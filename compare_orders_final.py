import os
import sys
import django
import pandas as pd

# Django ayarları
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order, OrderItem
from products.models import Product
from customers.models import Customer
from django.db.models import Count

# Excel dosyasını oku
df = pd.read_excel('/Users/emreuysal/Downloads/siparis_excel_sablonu.xlsx')

print("=== EXCEL VE VERİTABANI KARŞILAŞTIRMASI ===\n")

# Sipariş analizi
excel_order_numbers = set(df['SIPARIŞ NO'].unique())
db_order_numbers = set(Order.objects.values_list('order_number', flat=True))

print("SİPARİŞ ANALİZİ:")
print(f"Excel'deki benzersiz sipariş sayısı: {len(excel_order_numbers)}")
print(f"Veritabanındaki benzersiz sipariş sayısı: {len(db_order_numbers)}")

# Eksik siparişler
missing_orders = excel_order_numbers - db_order_numbers
print(f"\nVeritabanında olmayan sipariş sayısı: {len(missing_orders)}")
if missing_orders:
    print("Eksik siparişler:")
    for order_no in missing_orders:
        excel_rows = df[df['SIPARIŞ NO'] == order_no]
        print(f"  - {order_no}")
        print(f"    Müşteri: {excel_rows.iloc[0]['MÜŞTERI ISMI']}")
        print(f"    Tarih: {excel_rows.iloc[0]['SIPARIŞ TARIHI VE SAATI']}")
        print(f"    SKU: {excel_rows.iloc[0]['SKU']}")

# Sipariş öğesi analizi
print("\n\nSİPARİŞ ÖĞESİ ANALİZİ:")
order_item_count_db = OrderItem.objects.count()
print(f"Veritabanındaki sipariş öğesi sayısı: {order_item_count_db}")
print(f"Excel'deki satır sayısı: {len(df)}")
print(f"Fark: {len(df) - order_item_count_db}")

# Öğe sayısı farklı olan siparişler
db_order_items = OrderItem.objects.values('order__order_number').annotate(count=Count('id'))
db_order_counts = {item['order__order_number']: item['count'] for item in db_order_items}
excel_order_counts = df['SIPARIŞ NO'].value_counts().to_dict()

common_orders = excel_order_numbers & db_order_numbers
diff_orders = []
for order_no in common_orders:
    excel_count = excel_order_counts.get(order_no, 0)
    db_count = db_order_counts.get(order_no, 0)
    if excel_count != db_count:
        diff_orders.append((order_no, excel_count, db_count))

print(f"\nÖğe sayısı farklı olan sipariş sayısı: {len(diff_orders)}")
if diff_orders:
    print("Detaylar:")
    for order_no, excel_count, db_count in diff_orders:
        print(f"  {order_no}: Excel={excel_count}, DB={db_count}, Fark={excel_count - db_count}")
        # Hangi ürünler eksik?
        excel_items = df[df['SIPARIŞ NO'] == order_no]
        order = Order.objects.get(order_number=order_no)
        db_skus = set(order.items.values_list('product__sku', flat=True))
        excel_skus = set(excel_items['SKU'])
        missing_skus = excel_skus - db_skus
        if missing_skus:
            print(f"    Eksik SKU'lar: {missing_skus}")

# Müşteri analizi
print("\n\nMÜŞTERİ ANALİZİ:")
excel_customers = set(df['MÜŞTERI ISMI'].unique())
print(f"Excel'deki benzersiz müşteri sayısı: {len(excel_customers)}")
print(f"Veritabanındaki müşteri sayısı: {Customer.objects.count()}")

missing_customers = []
for customer_name in excel_customers:
    if not Customer.objects.filter(name__iexact=customer_name).exists():
        missing_customers.append(customer_name)

print(f"Veritabanında olmayan müşteri sayısı: {len(missing_customers)}")
if missing_customers:
    print("Eksik müşteriler:")
    for name in missing_customers[:5]:  # İlk 5
        print(f"  - {name}")

# Ürün analizi
print("\n\nÜRÜN ANALİZİ:")
excel_skus = set(df['SKU'].unique())
db_skus = set(Product.objects.values_list('sku', flat=True))
missing_skus = excel_skus - db_skus

print(f"Excel'deki benzersiz SKU sayısı: {len(excel_skus)}")
print(f"Veritabanındaki ürün sayısı: {Product.objects.count()}")
print(f"Veritabanında olmayan SKU sayısı: {len(missing_skus)}")
if missing_skus:
    print("Eksik SKU'lar ve ürünleri:")
    for sku in missing_skus:
        excel_product = df[df['SKU'] == sku].iloc[0]
        print(f"  - SKU: {sku}")
        print(f"    Ürün: {excel_product['ÜRÜN ISMI']}")
        print(f"    GTIN: {excel_product['GTIN'] if not pd.isna(excel_product['GTIN']) else 'Yok'}")

# Özet
print("\n\n=== ÖZET ===")
print(f"Toplam eksik sipariş: {len(missing_orders)}")
print(f"Toplam eksik sipariş öğesi: {len(df) - order_item_count_db}")
print(f"Toplam eksik müşteri: {len(missing_customers)}")
print(f"Toplam eksik ürün: {len(missing_skus)}")

print("\n\nÖNERİLEN ÇÖZÜM:")
print("1. Yeni geliştirilen enhanced_import_orders_excel fonksiyonu kullanıldığında:")
print("   - Eksik müşteriler otomatik oluşturulacak")
print("   - Eksik ürünler otomatik oluşturulacak")
print("   - GTIN/Barcode eşleştirmesi düzgün yapılacak")
print("   - Detaylı import log'u tutulacak")
print("2. Import sonrası /orders/import-tasks/ sayfasından detaylar görüntülenebilir")