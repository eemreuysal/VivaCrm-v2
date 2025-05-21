#!/usr/bin/env python
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.excel import ExcelImporter
from products.models import Product

def test_field_mapping():
    """Test field mapping normalization"""
    
    # Define the same field mapping as in products/excel.py
    field_mapping = {
        'Product Code *': 'code',
        'Product Code': 'code',
        'Product Name *': 'name',
        'Product Name': 'name',
        'Category *': 'category',
        'Category': 'category',
        'Price *': 'price',
        'Price': 'price',
        'Initial Stock *': 'current_stock',
        'Initial Stock': 'current_stock',
        'Current Stock': 'current_stock',
    }
    
    # Test columns from Excel
    test_columns = [
        'Product Code *',
        'Product Name *', 
        'Category',
        'Price *',
        'Initial Stock *'
    ]
    
    # Create importer instance
    importer = ExcelImporter(
        model=Product,
        field_mapping=field_mapping,
        required_fields=['code', 'name', 'category', 'price', 'current_stock']
    )
    
    print("Testing field name normalization:")
    print("=" * 50)
    
    for column in test_columns:
        normalized = importer._normalize_field_name(column)
        expected = field_mapping.get(column, column.lower().replace(' ', '_'))
        print(f"Column: '{column}'")
        print(f"  Normalized: '{normalized}'")
        print(f"  Expected: '{expected}'")
        print(f"  Match: {normalized == expected}")
        print()
        
    # Test the exact normalization logic
    print("\nDetailed normalization check:")
    print("=" * 50)
    
    # Field mapping check
    print("\nField mapping (case sensitive):")
    for excel_name, field_name in field_mapping.items():
        print(f"  '{excel_name}' -> '{field_name}'")
    
    print("\nField mapping (lowercase):")
    for excel_name, field_name in field_mapping.items():
        lower_match = excel_name.lower() == 'category'.lower()
        print(f"  '{excel_name}'.lower() == 'category'.lower(): {lower_match}")

if __name__ == "__main__":
    test_field_mapping()