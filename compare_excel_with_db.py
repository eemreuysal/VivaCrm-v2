#!/usr/bin/env python
"""
Excel dosyasını veritabanı ile karşılaştır
"""
import os
import sys
import django
import pandas as pd
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product
from orders.models import Order, OrderItem
from customers.models import Customer


def compare_excel_with_database(excel_path):
    """Excel dosyasını veritabanı ile karşılaştır"""
    
    print(f"Excel dosyası okunuyor: {excel_path}")
    
    try:
        # Excel dosyasını oku
        df = pd.read_excel(excel_path)
        print(f"Excel'de toplam {len(df)} satır bulundu")
        print(f"Sütunlar: {list(df.columns)}")
        
        # Sütun isimlerini normalize et
        df.columns = [col.strip().upper() for col in df.columns]
        
        # Önce sütunları kontrol edelim
        print("\n=== EXCEL SÜTUNLARI ===")
        for col in df.columns:
            print(f"- {col}")
        
        # Veritabanındaki ürün sayısı
        db_product_count = Product.objects.count()
        print(f"\nVeritabanında toplam {db_product_count} ürün var")
        
        # Excel'deki ürün kodlarını kontrol et
        if 'ÜRÜN KODU' in df.columns or 'URUNKODU' in df.columns or 'PRODUCT CODE' in df.columns:
            code_column = None
            for col in ['ÜRÜN KODU', 'URUNKODU', 'PRODUCT CODE', 'CODE']:
                if col in df.columns:
                    code_column = col
                    break
            
            if code_column:
                excel_codes = set(df[code_column].dropna().astype(str).str.strip())
                db_codes = set(Product.objects.values_list('code', flat=True))
                
                print(f"\nExcel'de {len(excel_codes)} benzersiz ürün kodu var")
                print(f"Veritabanında {len(db_codes)} benzersiz ürün kodu var")
                
                # Excel'de olup veritabanında olmayan kodlar
                missing_in_db = excel_codes - db_codes
                if missing_in_db:
                    print(f"\nExcel'de olup veritabanında OLMAYAN {len(missing_in_db)} kod:")
                    for code in list(missing_in_db)[:10]:  # İlk 10 tanesini göster
                        row = df[df[code_column] == code].iloc[0]
                        name_col = None
                        for col in ['ÜRÜN ADI', 'URUNISMI', 'PRODUCT NAME', 'NAME']:
                            if col in df.columns:
                                name_col = col
                                break
                        name = row[name_col] if name_col else 'N/A'
                        print(f"  - {code}: {name}")
                    
                    if len(missing_in_db) > 10:
                        print(f"  ... ve {len(missing_in_db) - 10} kod daha")
                
                # Veritabanında olup Excel'de olmayan kodlar
                missing_in_excel = db_codes - excel_codes
                if missing_in_excel:
                    print(f"\nVeritabanında olup Excel'de OLMAYAN {len(missing_in_excel)} kod:")
                    for code in list(missing_in_excel)[:10]:
                        product = Product.objects.get(code=code)
                        print(f"  - {code}: {product.name}")
                    
                    if len(missing_in_excel) > 10:
                        print(f"  ... ve {len(missing_in_excel) - 10} kod daha")
        
        # Sipariş kontrolü (eğer sipariş dosyasıysa)
        if 'SİPARİŞ NO' in df.columns or 'ORDER NUMBER' in df.columns:
            order_column = None
            for col in ['SİPARİŞ NO', 'ORDER NUMBER', 'ORDER_NUMBER']:
                if col in df.columns:
                    order_column = col
                    break
            
            if order_column:
                excel_orders = set(df[order_column].dropna().astype(str).str.strip())
                db_orders = set(Order.objects.values_list('order_number', flat=True))
                
                print(f"\nExcel'de {len(excel_orders)} benzersiz sipariş var")
                print(f"Veritabanında {len(db_orders)} benzersiz sipariş var")
                
                missing_orders = excel_orders - db_orders
                if missing_orders:
                    print(f"\nExcel'de olup veritabanında OLMAYAN {len(missing_orders)} sipariş:")
                    for order_no in list(missing_orders)[:10]:
                        print(f"  - {order_no}")
        
        # Müşteri kontrolü
        if 'MÜŞTERİ' in df.columns or 'CUSTOMER' in df.columns:
            customer_column = None
            for col in ['MÜŞTERİ', 'CUSTOMER', 'MÜŞTERİ ADI']:
                if col in df.columns:
                    customer_column = col
                    break
            
            if customer_column:
                excel_customers = set(df[customer_column].dropna().astype(str).str.strip())
                db_customers = set(Customer.objects.values_list('full_name', flat=True))
                
                print(f"\nExcel'de {len(excel_customers)} benzersiz müşteri var")
                print(f"Veritabanında {len(db_customers)} benzersiz müşteri var")
        
        # Detaylı satır analizi
        print("\n=== DETAYLI SATIR ANALİZİ ===")
        print(f"Excel'deki ilk 5 satır:")
        print(df.head())
        
        # Boş satırları kontrol et
        empty_rows = df[df.isnull().all(axis=1)]
        if not empty_rows.empty:
            print(f"\nExcel'de {len(empty_rows)} boş satır var")
        
        # Eksik değerleri kontrol et
        print("\nEksik değer sayısı (sütuna göre):")
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                print(f"  {col}: {null_count} eksik değer")
        
        return {
            'excel_rows': len(df),
            'db_products': db_product_count,
            'missing_in_db': list(missing_in_db) if 'missing_in_db' in locals() else [],
            'missing_in_excel': list(missing_in_excel) if 'missing_in_excel' in locals() else [],
            'columns': list(df.columns)
        }
        
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def check_specific_product(code):
    """Belirli bir ürünü kontrol et"""
    try:
        product = Product.objects.get(code=code)
        print(f"\nÜrün bulundu: {product.name}")
        print(f"  Kod: {product.code}")
        print(f"  Fiyat: {product.price}")
        print(f"  Stok: {product.stock}")
        print(f"  Kategori: {product.category}")
        return product
    except Product.DoesNotExist:
        print(f"\nÜrün bulunamadı: {code}")
        return None


if __name__ == "__main__":
    excel_file = "/Users/emreuysal/Downloads/siparis_excel_sablonu.xlsx"
    
    if os.path.exists(excel_file):
        result = compare_excel_with_database(excel_file)
        
        # Özet bilgi
        if result:
            print("\n=== ÖZET ===")
            print(f"Excel satır sayısı: {result['excel_rows']}")
            print(f"DB ürün sayısı: {result['db_products']}")
            print(f"Excel'de olup DB'de olmayan: {len(result['missing_in_db'])}")
            print(f"DB'de olup Excel'de olmayan: {len(result['missing_in_excel'])}")
            
            # Eksik ürünleri detaylı yazdır
            if result['missing_in_db']:
                print("\n=== YÜKLENMEMIŞ ÜRÜNLER ===")
                with open('missing_products.txt', 'w', encoding='utf-8') as f:
                    for code in result['missing_in_db']:
                        f.write(f"{code}\n")
                print("Eksik ürünler 'missing_products.txt' dosyasına kaydedildi")
    else:
        print(f"Excel dosyası bulunamadı: {excel_file}")