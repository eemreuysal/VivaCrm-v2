#!/usr/bin/env python3
"""
Debug the import issue directly.
"""

import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, Category
from products.excel_smart_import import import_products_smart

def test_direct_import():
    """Test the import directly without the view."""
    
    # Read the Excel file
    excel_file_path = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
    
    print(f"Testing direct import from: {excel_file_path}")
    
    # Get initial counts
    initial_product_count = Product.objects.count()
    initial_category_count = Category.objects.count()
    
    print(f"Initial products: {initial_product_count}")
    print(f"Initial categories: {initial_category_count}")
    
    # Test direct import
    try:
        result = import_products_smart(
            file_path=excel_file_path,
            show_warnings=False
        )
        
        print("\nImport result:")
        print(f"Success: {result['success']}")
        print(f"Stats: {result['stats']}")
        
        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
                
    except Exception as e:
        print(f"\nException during import: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Check final counts
    final_product_count = Product.objects.count()
    final_category_count = Category.objects.count()
    
    print(f"\nFinal products: {final_product_count}")
    print(f"Final categories: {final_category_count}")
    print(f"Products added/updated: {final_product_count - initial_product_count}")
    print(f"Categories created: {final_category_count - initial_category_count}")


if __name__ == '__main__':
    test_direct_import()