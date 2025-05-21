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

def test_category_import():
    """Test product import with various category names"""
    
    # Create test Excel data matching the correct column names
    test_data = {
        'Product Code *': ['TEST-001', 'TEST-002', 'TEST-003', 'TEST-004', 'TEST-005'],
        'Product Name *': [
            'Test Pom Pom Havlu',
            'Test Waffle Bornoz', 
            'Test Muslin Battaniye',
            'Test Stonewashed Nevresim',
            'Test Cabana Havlu'
        ],
        'Category': [
            'Pom Pom Towel',
            'waffle bathrobe',  # Test case insensitive
            'MUSLIN BLANKET',   # Test uppercase
            'Stonewashed Duvet Cover',
            'cabana towel'      # Test lowercase
        ],
        'Price *': [150.00, 250.00, 180.00, 320.00, 195.00],
        'Initial Stock *': [100, 50, 75, 60, 80],
        'Tax Rate (%)': [20, 20, 20, 20, 20],
        'SKU': ['TEST-001', 'TEST-002', 'TEST-003', 'TEST-004', 'TEST-005']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(test_data)
    test_file = 'test_category_import.xlsx'
    df.to_excel(test_file, index=False)
    
    print("Created test Excel file with category variations")
    print("=" * 50)
    
    # Get admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("Creating admin user for test...")
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
        print(f"Created: {len(result.created_ids)} products")
        print(f"Updated: {len(result.updated_ids)} products")
        
        if result.errors:
            print("\nErrors encountered:")
            for error in result.errors:
                print(f"  - {error}")
        
        # Verify imported products
        print("\nVerifying imported products:")
        for code in test_data['Product Code *']:
            product = Product.objects.filter(code=code).first()
            if product:
                print(f"  ✓ {product.code}: {product.name} -> Category: {product.category.name}")
            else:
                print(f"  ✗ {code}: Not found")
                
    except Exception as e:
        print(f"Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\nCleaned up test file: {test_file}")

if __name__ == "__main__":
    test_category_import()