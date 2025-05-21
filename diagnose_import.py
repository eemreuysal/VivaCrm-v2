#!/usr/bin/env python
import os
import sys
import django
import pandas as pd
from io import BytesIO

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.excel import ExcelImporter
from products.models import Product, Category
from products.excel import import_products_excel

def diagnose_import():
    """Diagnose the import issue"""
    
    # Create test data
    data = {
        'Product Code *': ['DIAGTEST001'],
        'Product Name *': ['Diagnostic Test Product'],
        'Category': ['Waffle Towel'],
        'Price *': [100.0],
        'Initial Stock *': [50]
    }
    
    df = pd.DataFrame(data)
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    print("Original DataFrame:")
    print(df)
    print("\nColumns:", df.columns.tolist())
    
    # Let's manually step through what import_products_excel does
    print("\n" + "="*50)
    print("Manual Import Process:")
    print("="*50)
    
    # Read the Excel file
    excel_buffer.seek(0)
    df_read = pd.read_excel(excel_buffer)
    print("\n1. Read Excel file:")
    print("   Columns:", df_read.columns.tolist())
    
    # Remove unnamed columns and fill NaN
    df_processed = df_read.loc[:, ~df_read.columns.str.contains('^Unnamed')]
    df_processed = df_processed.fillna('')
    print("\n2. After processing:")
    print("   Columns:", df_processed.columns.tolist())
    
    # Check field mapping
    field_mapping = {
        'Product Code *': 'code',
        'Product Name *': 'name',  
        'Category': 'category',
        'Price *': 'price',
        'Initial Stock *': 'current_stock',
    }
    
    print("\n3. Field Mapping:")
    for excel_col, model_field in field_mapping.items():
        print(f"   '{excel_col}' -> '{model_field}'")
    
    # Process first row
    first_row = df_processed.iloc[0]
    print("\n4. First row data:")
    for col, val in first_row.items():
        print(f"   '{col}': {val}")
    
    # Test normalization
    importer = ExcelImporter(
        model=Product,
        field_mapping=field_mapping,
        required_fields=['code', 'name', 'category', 'price', 'current_stock']
    )
    
    print("\n5. Field normalization:")
    normalized_data = {}
    for col, val in first_row.items():
        normalized_field = importer._normalize_field_name(col)
        normalized_data[normalized_field] = val
        print(f"   '{col}' -> '{normalized_field}': {val}")
    
    print("\n6. Checking required fields:")
    for field in importer.required_fields:
        if field in normalized_data:
            print(f"   ✓ '{field}' found with value: {normalized_data[field]}")
        else:
            print(f"   ✗ '{field}' NOT FOUND")
    
    # Now let's check the actual import process
    print("\n" + "="*50)
    print("Actual Import Process:")
    print("="*50)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    
    excel_buffer.seek(0)
    try:
        result = import_products_excel(excel_buffer, user=user)
        print("Import completed")
        print(f"Success: {result.success}")
        print(f"Failed: {result.failed}")
        print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_import()