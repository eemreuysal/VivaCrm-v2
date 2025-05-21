#!/usr/bin/env python
import os
import sys
import django
import pandas as pd
import json
from datetime import datetime

# Django ayarlarını yükle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order, OrderItem
from customers.models import Customer
from products.models import Product
from core.models_import import ImportTask
from django.db import models

# Eksik siparişlerin detaylı analizi
missing_order_numbers = [
    '113-8018173-8677847',
    '114-2274879-7067409', 
    '114-2796436-6786643'
]

# Excel dosyasını oku
excel_path = '/Users/emreuysal/Downloads/siparis_excel_sablonu.xlsx'
print(f"Excel dosyası okunuyor: {excel_path}")

try:
    df = pd.read_excel(excel_path)
    
    # Order modelinin yapısını kontrol et
    print("\n=== Order MODEL YAPISI ===")
    print(f"Order model fields: {[f.name for f in Order._meta.fields]}")
    print(f"Order model unique fields: {[f.name for f in Order._meta.fields if f.unique]}")
    
    # ImportTask kayıtlarını kontrol et
    print("\n=== IMPORT TASK KAYITLARI ===")
    try:
        import_tasks = ImportTask.objects.filter(type='order').order_by('-created_at')[:10]
        for task in import_tasks:
            print(f"Task {task.id}: {task.status} - {task.created_at}")
            # DetailedImportResult'ları kontrol et
            failed_results = task.detailed_results.filter(status='failed')
            if failed_results.exists():
                print(f"  Başarısız satırlar:")
                for result in failed_results[:5]:
                    print(f"    Satır {result.row_number}: {result.error_message}")
                    if result.data:
                        for order_no in missing_order_numbers:
                            data_str = str(result.data)
                            if order_no in data_str:
                                print(f"      >>> EKSİK SİPARİŞ BULUNDU: {order_no}")
                                print(f"      Veri: {result.data}")
                                print(f"      Hata: {result.error_details}")
    except Exception as e:
        print(f"Import task kontrolünde hata: {e}")
    
    # Eksik siparişleri detaylı incele
    print("\n=== EKSİK SİPARİŞ ANALİZİ ===")
    for order_no in missing_order_numbers:
        print(f"\nSipariş No: {order_no}")
        
        # Excel'deki satırları al
        excel_rows = df[df['SIPARIŞ NO'] == order_no]
        print(f"Excel'de {len(excel_rows)} satır bulundu")
        
        if not excel_rows.empty:
            row = excel_rows.iloc[0]
            
            # Müşteri bilgisini kontrol et
            customer_name = row['MÜŞTERI ISMI']
            print(f"Müşteri: {customer_name}")
            print(f"Customer model fields: {[f.name for f in Customer._meta.fields]}")
            
            # Customer modeli name alanı kullanıyor (first_name/last_name yerine)
            # Müşteriyi veritabanında ara
            customers = Customer.objects.filter(name__icontains=customer_name.split(' - ')[0])
            if customers.exists():
                print(f"  Müşteri bulundu: {customers.count()} eşleşme")
                for c in customers:
                    print(f"    - {c.id}: {c.name}")
            else:
                print(f"  Müşteri BULUNAMADI: {customer_name}")
                
                # Alternatif aramalar
                alt_customers = Customer.objects.filter(
                    models.Q(name__icontains=customer_name.split()[0]) |
                    models.Q(email__icontains=customer_name.lower().replace(' ', '.'))
                )
                if alt_customers.exists():
                    print(f"  Alternatif müşteriler (isim veya email benzerliği):")
                    for c in alt_customers[:5]:
                        print(f"    - {c.id}: {c.name} ({c.email})")
            
            # Ürün bilgilerini kontrol et
            sku = row['SKU']
            print(f"SKU: {sku}")
            
            try:
                product = Product.objects.get(sku=sku)
                print(f"  Ürün bulundu: {product.id} - {product.name}")
            except Product.DoesNotExist:
                print(f"  Ürün BULUNAMADI: {sku}")
                
                # Alternatif ürün aramaları
                alt_products = Product.objects.filter(sku__icontains=sku[:5])
                if alt_products.exists():
                    print(f"  Alternatif ürünler (benzer SKU):")
                    for p in alt_products[:5]:
                        print(f"    - {p.sku}: {p.name}")
            
            # Tarih formatını kontrol et
            order_date = row['SIPARIŞ TARIHI VE SAATI']
            print(f"Tarih: {order_date}")
            
            # Potansiyel sorunları özetle
            print("\nPOTANSİYEL SORUNLAR:")
            
            # 1. Müşteri eşleşmemesi
            if not Customer.objects.filter(name__icontains=customer_name.split(' - ')[0]).exists():
                print("  - Müşteri ismi eşleşmemesi")
            
            # 2. Ürün eşleşmemesi
            if not Product.objects.filter(sku=sku).exists():
                print("  - Ürün SKU eşleşmemesi")
            
            # 3. Tarih formatı
            try:
                # Farklı tarih formatlarını dene
                date_formats = [
                    '%d.%m.%Y %H:%M',
                    '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %H:%M',
                    '%d/%m/%Y %H:%M'
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(str(order_date), fmt)
                        print(f"  Tarih formatı OK: {fmt}")
                        break
                    except ValueError:
                        continue
                
                if not parsed_date:
                    print("  - Tarih formatı tanınamadı")
            except Exception as e:
                print(f"  - Tarih parse hatası: {e}")
            
            # 4. Tekrar eden sipariş kontrolü
            duplicate_check = Order.objects.filter(order_number=order_no)
            if duplicate_check.exists():
                print(f"  - Bu sipariş numarası zaten mevcut! (ID: {duplicate_check.first().id})")
    
    # İlgili log dosyalarını kontrol et
    print("\n=== LOG DOSYALARI ===")
    log_files = [
        '/Users/emreuysal/Documents/Project/VivaCrm v2/logs/vivacrm.log',
        '/Users/emreuysal/Documents/Project/VivaCrm v2/logs/error.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\nLog dosyası: {log_file}")
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Son 100 satırdan ilgili olanları bul
                relevant_lines = []
                for line in lines[-100:]:
                    for order_no in missing_order_numbers:
                        if order_no in line:
                            relevant_lines.append(line.strip())
                
                if relevant_lines:
                    print("İlgili log satırları:")
                    for line in relevant_lines[-10:]:  # Son 10 satır
                        print(f"  {line}")
    
except Exception as e:
    print(f"Hata oluştu: {e}")
    import traceback
    traceback.print_exc()