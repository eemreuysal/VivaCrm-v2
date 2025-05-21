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
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

def test_stock_field():
    """Test that stock field is working correctly"""
    
    # Create test data with stock field
    test_data = {
        'Ürün Kodu': ['STOCK-001'],
        'URUNISMI': ['Stock Test Ürün'],
        'Kategori': ['Waffle Towel'],
        'FIYAT': [150.00],
        'STOK': [100],  # This should map to 'stock' field
        'BARKOD': ['1234567890']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(test_data)
    test_file = 'test_stock_field.xlsx'
    df.to_excel(test_file, index=False)
    
    print("Test file created with columns:", df.columns.tolist())
    print(df)
    print("=" * 50)
    
    # Get admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='test_admin',
            email='test@example.com',
            password='testpass123'
        )
    
    # Run import
    try:
        with open(test_file, 'rb') as f:
            result = ProductExcelImport.import_data(f, user=admin_user)
            
        print(f"Import completed!")
        print(f"Success: {result.success} products")
        print(f"Failed: {result.failed} products")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
        
        # Verify the imported product
        product = Product.objects.filter(code='STOCK-001').first()
        if product:
            print(f"\nProduct imported successfully:")
            print(f"  Code: {product.code}")
            print(f"  Name: {product.name}")
            print(f"  Stock: {product.stock}")  # This should be 100
        else:
            print("\nProduct not found")
                
    except Exception as e:
        print(f"Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\nTest file cleaned up")
        
        # Clean test products
        Product.objects.filter(code='STOCK-001').delete()
        print("Test product cleaned up")

if __name__ == "__main__":
    test_stock_field()