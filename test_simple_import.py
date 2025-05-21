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

def test_simple_import():
    """Test a simple Excel import"""
    
    # Create a simple Excel file in memory
    data = {
        'Product Code *': ['TEST001'],
        'Product Name *': ['Test Product'],
        'Category': ['Waffle Towel'],
        'Price *': [100.0],
        'Initial Stock *': [50]
    }
    
    df = pd.DataFrame(data)
    
    # Save to BytesIO
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    print("Excel data:")
    print(df)
    print("\nColumns:", df.columns.tolist())
    
    # Try importing
    from products.excel import ProductExcelImport
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    
    try:
        result = ProductExcelImport.import_data(excel_buffer, user=user)
        print(f"\nImport successful!")
        print(f"Success: {result.success}")
        print(f"Failed: {result.failed}")
        print(f"Errors: {result.errors}")
        
    except Exception as e:
        print(f"\nImport failed: {e}")
        
        # Let's manually check the import process
        from core.excel import ExcelImporter
        from products.models import Product
        
        # Define the same field mapping as in the product importer
        field_mapping = {
            'Product Code *': 'code',
            'Product Name *': 'name',
            'Category': 'category',
            'Price *': 'price',
            'Initial Stock *': 'current_stock',
        }
        
        importer = ExcelImporter(
            model=Product,
            field_mapping=field_mapping,
            required_fields=['code', 'name', 'category', 'price', 'current_stock']
        )
        
        # Read the Excel file manually
        excel_buffer.seek(0)
        df_test = pd.read_excel(excel_buffer)
        print("\nManual Excel read:")
        print("Columns:", df_test.columns.tolist())
        
        # Test normalization
        print("\nField normalization test:")
        for col in df_test.columns:
            normalized = importer._normalize_field_name(col)
            print(f"  '{col}' -> '{normalized}'")
            
        # Check missing fields
        missing = importer._validate_required_fields(df_test)
        print(f"\nMissing fields: {missing}")

if __name__ == "__main__":
    test_simple_import()