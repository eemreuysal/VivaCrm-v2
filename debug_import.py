#!/usr/bin/env python
import os
import sys
import django
import pandas as pd

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.excel import import_products_excel
from products.models import Product, Category
from django.contrib.auth import get_user_model

def debug_excel_import():
    """Debug Excel import to check column mapping"""
    
    # Create test Excel data
    test_data = {
        'Product Code *': ['TEST-001'],
        'Product Name *': ['Test Product'],
        'Category': ['Waffle Towel'],
        'Price *': [100.00],
        'Initial Stock *': [50]
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(test_data)
    test_file = 'debug_import.xlsx'
    df.to_excel(test_file, index=False)
    
    print("Created test Excel file")
    print("Columns in Excel:", df.columns.tolist())
    print("Sample data:")
    print(df)
    print("=" * 50)
    
    # Read the file back to see how it's being processed
    df_read = pd.read_excel(test_file)
    print("\nColumns after reading Excel back:")
    print(df_read.columns.tolist())
    
    # Check if columns exactly match
    for col in df_read.columns:
        print(f"  Column: '{col}' (type: {type(col).__name__})")
    
    print("\n" + "=" * 50)
    
    # Get admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='test_admin',
            email='test@example.com',
            password='testpass123'
        )
    
    # Check category existence
    print("\nChecking categories:")
    for cat in Category.objects.all():
        print(f"  - {cat.name}")
    
    # Run import with debug
    try:
        print("\nRunning import...")
        with open(test_file, 'rb') as f:
            # Read first few lines to debug
            f.seek(0)
            import openpyxl
            wb = openpyxl.load_workbook(f)
            ws = wb.active
            headers = [cell.value for cell in ws[1]]
            print("Headers from openpyxl:", headers)
            
            # Reset file position
            f.seek(0)
            result = import_products_excel(f, user=admin_user)
            
        print(f"\nImport result:")
        print(f"  Success: {result.success}")
        print(f"  Failed: {result.failed}")
        print(f"  Errors: {result.errors}")
        
    except Exception as e:
        print(f"Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\nCleaned up test file")

if __name__ == "__main__":
    debug_excel_import()