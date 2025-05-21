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

# Excel dosyasını oku
excel_path = '/Users/emreuysal/Downloads/siparis_excel_sablonu.xlsx'
print(f"Excel dosyası okunuyor: {excel_path}")

try:
    df = pd.read_excel(excel_path)
    print(f"Excel'de {len(df)} satır bulundu.")
    
    # Eksik sütunları kontrol et
    print("\nExcel sütunları:", list(df.columns))
    
    # Sipariş numaralarını al (SIPARIS_NO veya SIPARIS_NUMARASI sütunu)
    order_no_column = None
    for col in ['SIPARIŞ NO', 'SIPARIS NO', 'SIPARIS_NO', 'SIPARIS_NUMARASI', 'SiparişNumarası', 'Order Number']:
        if col in df.columns:
            order_no_column = col
            break
    
    if not order_no_column:
        print("HATA: Sipariş numarası sütunu bulunamadı!")
        print("Kullanılabilir sütunlar:", list(df.columns))
        sys.exit(1)
    
    # Excel'deki sipariş numaralarını al
    excel_order_numbers = set(df[order_no_column].astype(str).str.strip())
    print(f"\nExcel'de {len(excel_order_numbers)} benzersiz sipariş bulundu.")
    
    # Veritabanındaki siparişleri al
    db_orders = Order.objects.all()
    db_order_numbers = set(str(o.order_number).strip() for o in db_orders)
    print(f"Veritabanında {len(db_order_numbers)} sipariş bulundu.")
    
    # Eksik siparişleri bul (Excel'de var ama veritabanında yok)
    missing_in_db = excel_order_numbers - db_order_numbers
    print(f"\nExcel'de var ama veritabanında yok: {len(missing_in_db)} sipariş")
    
    if missing_in_db:
        print("\nEksik siparişler (ilk 20):")
        for i, order_no in enumerate(sorted(missing_in_db)[:20]):
            rows = df[df[order_no_column].astype(str).str.strip() == order_no]
            if not rows.empty:
                row = rows.iloc[0]
                print(f"{i+1}. Sipariş No: {order_no}")
                # Mevcut sütun adlarına göre bilgileri göster
                for col in df.columns:
                    if col != order_no_column and pd.notna(row[col]):
                        print(f"   {col}: {row[col]}")
                print()
    
    # Fazla siparişleri bul (Veritabanında var ama Excel'de yok)
    extra_in_db = db_order_numbers - excel_order_numbers
    print(f"\nVeritabanında var ama Excel'de yok: {len(extra_in_db)} sipariş")
    
    if extra_in_db:
        print("\nFazla siparişler (ilk 20):")
        for i, order_no in enumerate(sorted(extra_in_db)[:20]):
            try:
                order = db_orders.get(order_number=order_no)
                print(f"{i+1}. Sipariş No: {order_no}, Müşteri: {order.customer}, Toplam: {order.total_amount}, Tarih: {order.created_at}")
            except Order.DoesNotExist:
                print(f"{i+1}. Sipariş No: {order_no} (detay bulunamadı)")
    
    # Tam eşleşenler
    matched_orders = excel_order_numbers & db_order_numbers
    print(f"\nTam eşleşen siparişler: {len(matched_orders)}")
    
    # Detaylı rapor
    print("\n=== DETAYLI RAPOR ===")
    print(f"Excel toplam satır: {len(df)}")
    print(f"Excel benzersiz sipariş: {len(excel_order_numbers)}")
    print(f"Veritabanı toplam sipariş: {len(db_orders)}")
    print(f"Veritabanı benzersiz sipariş: {len(db_order_numbers)}")
    print(f"Eşleşen siparişler: {len(matched_orders)}")
    print(f"Excel'de var DB'de yok: {len(missing_in_db)}")
    print(f"DB'de var Excel'de yok: {len(extra_in_db)}")
    
    # Müşteri bazlı analiz
    print("\n=== MÜŞTERİ ANALİZİ ===")
    customer_column = None
    for col in ['MÜŞTERI ISMI', 'MUSTERI ISMI', 'MUSTERI', 'MUSTERI_ADI', 'Customer', 'Customer Name']:
        if col in df.columns:
            customer_column = col
            break
    
    if customer_column:
        excel_customers = df[customer_column].value_counts()
        print(f"\nExcel'deki müşteriler (ilk 10):")
        for customer, count in excel_customers.head(10).items():
            if pd.notna(customer):
                print(f"- {customer}: {count} sipariş")
    
    # Eksik siparişlerin detaylı listesi JSON olarak kaydet
    missing_details = []
    for order_no in missing_in_db:
        rows = df[df[order_no_column].astype(str).str.strip() == order_no]
        if not rows.empty:
            row = rows.iloc[0]
            details = {'Order_Number': order_no}
            for col in df.columns:
                details[col] = str(row[col]) if pd.notna(row[col]) else ''
            missing_details.append(details)
    
    with open('missing_orders.json', 'w', encoding='utf-8') as f:
        json.dump(missing_details, f, ensure_ascii=False, indent=2)
        print(f"\nEksik siparişlerin detaylı listesi 'missing_orders.json' dosyasına kaydedildi.")
    
    # Veritabanındaki sipariş özetleri
    print("\n=== VERİTABANI SİPARİŞ ÖZETİ ===")
    if db_orders.exists():
        total_amount = sum(order.total_amount or 0 for order in db_orders)
        print(f"Toplam sipariş sayısı: {db_orders.count()}")
        print(f"Toplam tutar: {total_amount:.2f} TL")
        print(f"Ortalama sipariş tutarı: {total_amount/db_orders.count():.2f} TL")
        
        # Duruma göre siparişler
        from django.db.models import Count
        status_counts = db_orders.values('status').annotate(count=Count('id'))
        print("\nDuruma göre siparişler:")
        for status in status_counts:
            print(f"- {status['status']}: {status['count']} sipariş")
    
except Exception as e:
    print(f"Hata oluştu: {e}")
    import traceback
    traceback.print_exc()