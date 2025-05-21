#!/usr/bin/env python
import os
import sys
import django
import pandas as pd
import json

# Django ayarlarını yükle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product

# Excel dosyasını oku
excel_path = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
print(f"Excel dosyası okunuyor: {excel_path}")

try:
    df = pd.read_excel(excel_path)
    print(f"Excel'de {len(df)} satır bulundu.")
    
    # Excel'deki SKU'ları al
    excel_skus = set(df['SKU'].astype(str).str.strip())
    print(f"Excel'de {len(excel_skus)} benzersiz SKU bulundu.")
    
    # Veritabanındaki ürünleri al
    db_products = Product.objects.all()
    db_skus = set(str(p.sku).strip() for p in db_products)
    print(f"Veritabanında {len(db_skus)} ürün bulundu.")
    
    # Eksik ürünleri bul (Excel'de var ama veritabanında yok)
    missing_in_db = excel_skus - db_skus
    print(f"\nExcel'de var ama veritabanında yok: {len(missing_in_db)} ürün")
    
    if missing_in_db:
        print("\nEksik ürünler (ilk 20):")
        for i, sku in enumerate(sorted(missing_in_db)[:20]):
            row = df[df['SKU'].astype(str).str.strip() == sku].iloc[0]
            print(f"{i+1}. SKU: {sku}, Ürün: {row['URUNISMI']}, Kategori: {row.get('KATEGORI', 'N/A')}")
    
    # Fazla ürünleri bul (Veritabanında var ama Excel'de yok)
    extra_in_db = db_skus - excel_skus
    print(f"\nVeritabanında var ama Excel'de yok: {len(extra_in_db)} ürün")
    
    if extra_in_db:
        print("\nFazla ürünler (ilk 20):")
        for i, sku in enumerate(sorted(extra_in_db)[:20]):
            product = db_products.get(sku=sku)
            print(f"{i+1}. SKU: {sku}, Ürün: {product.name}, Kategori: {product.category}")
    
    # Tam eşleşenler
    matched_skus = excel_skus & db_skus
    print(f"\nTam eşleşen ürünler: {len(matched_skus)}")
    
    # Detaylı rapor
    print("\n=== DETAYLI RAPOR ===")
    print(f"Excel toplam satır: {len(df)}")
    print(f"Excel benzersiz SKU: {len(excel_skus)}")
    print(f"Veritabanı toplam ürün: {len(db_products)}")
    print(f"Veritabanı benzersiz SKU: {len(db_skus)}")
    print(f"Eşleşen ürünler: {len(matched_skus)}")
    print(f"Excel'de var DB'de yok: {len(missing_in_db)}")
    print(f"DB'de var Excel'de yok: {len(extra_in_db)}")
    
    # Kategori bazlı analiz
    print("\n=== KATEGORİ ANALİZİ ===")
    if 'KATEGORI' in df.columns:
        excel_categories = df['KATEGORI'].value_counts()
        print("\nExcel'deki kategoriler:")
        for cat, count in excel_categories.items():
            if pd.notna(cat):
                print(f"- {cat}: {count} ürün")
    
    # Eksik ürünlerin detaylı listesi JSON olarak kaydet
    missing_details = []
    for sku in missing_in_db:
        row = df[df['SKU'].astype(str).str.strip() == sku].iloc[0]
        missing_details.append({
            'SKU': sku,
            'URUNISMI': row['URUNISMI'],
            'KATEGORI': row.get('KATEGORI', ''),
            'FIYAT': str(row.get('FIYAT', '')),
            'BARKOD': row.get('BARKOD', ''),
            'ASIN': row.get('ASIN', '')
        })
    
    with open('missing_products.json', 'w', encoding='utf-8') as f:
        json.dump(missing_details, f, ensure_ascii=False, indent=2)
        print(f"\nEksik ürünlerin detaylı listesi 'missing_products.json' dosyasına kaydedildi.")
    
except Exception as e:
    print(f"Hata oluştu: {e}")
    import traceback
    traceback.print_exc()