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

# Excel dosyasını oku
df = pd.read_excel('/Users/emreuysal/Downloads/siparis_excel_sablonu.xlsx')

print("=== EKSIK SIPARIŞLER DETAYLI ANALİZ ===\n")

# Eksik siparişler
missing_orders = ['114-2796436-6786643', '114-2274879-7067409', '113-8018173-8677847']

for order_no in missing_orders:
    print(f"Sipariş No: {order_no}")
    excel_rows = df[df['SIPARIŞ NO'] == order_no]
    
    for idx, row in excel_rows.iterrows():
        print(f"  Müşteri: {row['MÜŞTERI ISMI']}")
        print(f"  Şehir: {row['ŞEHIR']}, Eyalet: {row['EYALET']}")
        print(f"  SKU: {row['SKU']}")
        print(f"  GTIN: {row['GTIN']}")
        print(f"  Ürün: {row['ÜRÜN ISMI']}")
        print(f"  Adet: {row['ADET']}")
        print(f"  Birim Fiyat: {row['BIRIM FIYAT']}")
        print(f"  Tarih: {row['SIPARIŞ TARIHI VE SAATI']}")
        
        # Müşteri kontrolü
        customer_name = row['MÜŞTERI ISMI'].strip()
        customer_exists = Customer.objects.filter(
            name__icontains=customer_name
        ).exists()
        print(f"  Müşteri mevcut mu?: {customer_exists}")
        
        # Ürün kontrolü
        sku = str(row['SKU'])
        product_exists = Product.objects.filter(sku=sku).exists()
        print(f"  Ürün mevcut mu? (SKU: {sku}): {product_exists}")
        
        # GTIN kontrolü (barcode alanı)
        if pd.notna(row['GTIN']):
            gtin = str(int(row['GTIN']))
            barcode_exists = Product.objects.filter(barcode=gtin).exists()
            print(f"  Ürün mevcut mu? (Barcode/GTIN: {gtin}): {barcode_exists}")
        else:
            print(f"  GTIN boş")
            
        print()
        
print("\n=== EKSIK SIPARIŞ ÖĞELERİ ===\n")

# Eksik öğeleri olan siparişler
partial_orders = [
    ('113-3705426-0579421', 2, 1),
    ('114-1985321-8075434', 3, 2)
]

for order_no, excel_count, db_count in partial_orders:
    print(f"Sipariş No: {order_no} (Excel: {excel_count}, DB: {db_count})")
    
    # Excel'deki öğeler
    excel_items = df[df['SIPARIŞ NO'] == order_no]
    print("Excel'deki öğeler:")
    for idx, row in excel_items.iterrows():
        print(f"  - SKU: {row['SKU']}, Ürün: {row['ÜRÜN ISMI']}")
    
    # Veritabanındaki öğeler
    order = Order.objects.filter(order_number=order_no).first()
    if order:
        db_items = OrderItem.objects.filter(order=order)
        print("Veritabanındaki öğeler:")
        for item in db_items:
            print(f"  - SKU: {item.product.sku if item.product else 'YOK'}, Ürün: {item.product.name if item.product else 'YOK'}")
    
    print()

# Özet analiz
print("\n=== ÖZET ===")
print("Eksik veriler ve muhtemel sebepler:")
print("\n1. Eksik Siparişler (3 adet):")
print("   - 114-2796436-6786643: Müşteri sistemde yok")
print("   - 114-2274879-7067409: Müşteri sistemde yok")
print("   - 113-8018173-8677847: Müşteri ve ürün (SKU: W3-J0CO-M6KV) sistemde yok")

print("\n2. Eksik Sipariş Öğeleri (2 siparişte toplam 2 öğe eksik):")
print("   - SKU: 7C-623E-1MC6 ürünü her iki siparişte de eksik")
print("   - Bu SKU'ya sahip ürün sistemde mevcut görünüyor ama ilişki kurulamamış")

print("\n3. GTIN/Barcode Uyumsuzluğu:")
print("   - Excel'deki GTIN değerleri, veritabanındaki barcode alanı ile eşleşmiyor")
print("   - Bu durum ürün eşleştirmesinde sorun yaratıyor olabilir")