#!/usr/bin/env python
import os
import sys
import django
import pandas as pd

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.excel import ProductExcelImport
from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

def test_turkish_import():
    """Türkçe sütun başlıklarıyla Excel import testi"""
    
    # Türkçe sütun başlıklarıyla test verisi oluştur
    test_data = {
        'Ürün Kodu': ['TURK-001', 'TURK-002'],
        'URUNISMI': ['Türkçe Test Ürün 1', 'Türkçe Test Ürün 2'],
        'Kategori': ['Waffle Towel', 'Muslin Towel'],
        'FIYAT': [150.00, 200.00],
        'stock_quantity': [100, 50],  # Problemli alan
        'BARKOD': ['1234567890', '0987654321']
    }
    
    # DataFrame oluştur ve Excel'e kaydet
    df = pd.DataFrame(test_data)
    test_file = 'test_turkish_import.xlsx'
    df.to_excel(test_file, index=False)
    
    print("Türkçe test Excel dosyası oluşturuldu")
    print("Sütunlar:", df.columns.tolist())
    print(df)
    print("=" * 50)
    
    # Admin kullanıcı al
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("Admin kullanıcı oluşturuluyor...")
        admin_user = User.objects.create_superuser(
            username='test_admin',
            email='test@example.com',
            password='testpass123'
        )
    
    # İçe aktarmayı çalıştır
    try:
        with open(test_file, 'rb') as f:
            result = ProductExcelImport.import_data(f, user=admin_user)
            
        print(f"İçe aktarma tamamlandı!")
        print(f"Başarılı: {result.success} ürün")
        print(f"Başarısız: {result.failed} ürün")
        print(f"Oluşturulan: {len(result.created_ids)} ürün")
        print(f"Güncellenen: {len(result.updated_ids)} ürün")
        
        if result.errors:
            print("\nHatalar:")
            for error in result.errors:
                print(f"  - {error}")
        
        # İçe aktarılan ürünleri doğrula
        print("\nİçe aktarılan ürünleri doğrulama:")
        for code in test_data['Ürün Kodu']:
            product = Product.objects.filter(code=code).first()
            if product:
                print(f"  ✓ {product.code}: {product.name} -> Kategori: {product.category.name}")
            else:
                print(f"  ✗ {code}: Bulunamadı")
                
    except Exception as e:
        print(f"İçe aktarma başarısız: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Temizlik
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\nTest dosyası temizlendi: {test_file}")
        
        # Test ürünlerini temizle
        Product.objects.filter(code__startswith='TURK-').delete()
        print("Test ürünleri temizlendi")

if __name__ == "__main__":
    test_turkish_import()