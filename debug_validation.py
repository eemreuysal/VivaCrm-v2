#!/usr/bin/env python
import os
import sys
import django
import pandas as pd

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.excel import ExcelImporter
from products.models import Product

def debug_validation():
    """Debug the validation logic"""
    
    # Test DataFrame
    data = {
        'Product Code *': ['TEST001'],
        'Product Name *': ['Test Product'],
        'Category': ['Waffle Towel'],
        'Price *': [100.0],
        'Initial Stock *': [50]
    }
    df = pd.DataFrame(data)
    
    # Field mapping from products/excel.py
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
        'Initial Stock': 'current_stock'
    }
    
    importer = ExcelImporter(
        model=Product,
        field_mapping=field_mapping,
        required_fields=['code', 'name', 'category', 'price', 'current_stock']
    )
    
    print("DataFrame columns:", df.columns.tolist())
    print("\nRequired fields:", importer.required_fields)
    
    # Step through validation
    print("\nValidation process:")
    normalized_columns = []
    for col in df.columns:
        normalized = importer._normalize_field_name(col)
        normalized_columns.append(normalized)
        print(f"  Column '{col}' -> '{normalized}'")
    
    print("\nNormalized columns:", normalized_columns)
    
    # Check each required field
    missing_fields = []
    for field in importer.required_fields:
        print(f"\nChecking required field: '{field}'")
        if field in normalized_columns:
            print(f"  ✓ Found in normalized columns")
        else:
            print(f"  ✗ NOT found in normalized columns")
            
            # This is where the bug happens
            excel_name = None
            for excel_col, model_field in field_mapping.items():
                if model_field == field:
                    excel_name = excel_col
                    print(f"  Found Excel mapping: '{excel_col}' -> '{model_field}'")
                    break
            
            if excel_name:
                print(f"  Bug: changing field from '{field}' to '{excel_name}'")
                field = excel_name  # This causes the bug!
            
            missing_fields.append(field)
    
    print(f"\nMissing fields: {missing_fields}")
    
    # Now let's test without the bug
    print("\n" + "="*50)
    print("Testing without the bug:")
    print("="*50)
    
    missing_fields_fixed = []
    for field in importer.required_fields:
        if field not in normalized_columns:
            missing_fields_fixed.append(field)  # Keep original field name
    
    print(f"Missing fields (fixed): {missing_fields_fixed}")

if __name__ == "__main__":
    debug_validation()