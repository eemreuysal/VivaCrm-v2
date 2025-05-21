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

def trace_import():
    """Trace the import process step by step"""
    
    # Create test data
    data = {
        'Product Code *': ['TRACE001'],
        'Product Name *': ['Trace Test Product'],
        'Category': ['Waffle Towel'],
        'Price *': [100.0],
        'Initial Stock *': [50]
    }
    
    df = pd.DataFrame(data)
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    print("Test DataFrame:")
    print(df)
    print("\nColumns:", df.columns.tolist())
    
    # Import the actual function
    from products.excel import import_products_excel
    from core.excel import ExcelImporter
    
    # Monkey patch the ExcelImporter to add debug output
    original_normalize = ExcelImporter._normalize_field_name
    original_validate = ExcelImporter._validate_required_fields
    
    def debug_normalize(self, name):
        result = original_normalize(self, name)
        print(f"  Normalize: '{name}' -> '{result}'")
        return result
    
    def debug_validate(self, df):
        print("\nValidating required fields:")
        print(f"  DataFrame columns: {df.columns.tolist()}")
        print(f"  Required fields: {self.required_fields}")
        result = original_validate(self, df)
        print(f"  Missing fields: {result}")
        return result
    
    ExcelImporter._normalize_field_name = debug_normalize
    ExcelImporter._validate_required_fields = debug_validate
    
    # Now run import
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    
    print("\n" + "="*50)
    print("Starting import...")
    print("="*50)
    
    excel_buffer.seek(0)
    try:
        result = import_products_excel(excel_buffer, user=user)
        print(f"\nImport completed: Success={result.success}, Failed={result.failed}")
        print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"\nImport failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Restore original methods
    ExcelImporter._normalize_field_name = original_normalize
    ExcelImporter._validate_required_fields = original_validate

if __name__ == "__main__":
    trace_import()