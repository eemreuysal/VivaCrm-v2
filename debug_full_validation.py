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
import pandas as pd
from io import BytesIO

# Create test data
data = {
    'Product Code *': ['DEBUG001'],
    'Product Name *': ['Debug Product'],
    'Category': ['Waffle Towel'],
    'Price *': [100.0],
    'Initial Stock *': [50]
}

df = pd.DataFrame(data)
excel_buffer = BytesIO()
df.to_excel(excel_buffer, index=False)
excel_buffer.seek(0)

# Monkey patch the import to add debug
original_import_data = ExcelImporter.import_data

def debug_import_data(self, file_obj, *args, **kwargs):
    print("=== IMPORT DATA DEBUG ===")
    
    # Process a row manually to see what's happening
    df = pd.read_excel(file_obj, sheet_name=0)
    df = df.fillna('')
    
    print(f"DataFrame columns: {df.columns.tolist()}")
    
    # Process first row
    first_row = df.iloc[0]
    print(f"\nFirst row: {first_row.to_dict()}")
    
    # Apply field mapping
    data = {}
    for column, value in first_row.items():
        field_name = self._normalize_field_name(column)
        print(f"  Column '{column}' -> field '{field_name}': {value}")
        
        # Apply validator if available
        if field_name in self.validators:
            try:
                value = self.validators[field_name](value)
                print(f"    After validator: {value} (type: {type(value)})")
            except Exception as e:
                print(f"    Validator error: {e}")
        
        data[field_name] = value
    
    print(f"\nProcessed data: {data}")
    
    # Check field validation
    print("\nField validation:")
    for field_name, value in data.items():
        try:
            field = self.model._meta.get_field(field_name)
            print(f"  {field_name}: {field.__class__.__name__}")
            field.clean(value, None)
            print(f"    ✓ Validation passed")
        except Exception as e:
            print(f"    ✗ Validation failed: {e}")
    
    # Now run the original import
    file_obj.seek(0)
    return original_import_data(self, file_obj, *args, **kwargs)

ExcelImporter.import_data = debug_import_data

# Run import
from products.excel import import_products_excel
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(is_superuser=True).first()

excel_buffer.seek(0)
try:
    result = import_products_excel(excel_buffer, user=user)
    print(f"\nImport result: Success={result.success}, Failed={result.failed}")
    print(f"Errors: {result.errors}")
except Exception as e:
    print(f"\nImport failed: {e}")
    import traceback
    traceback.print_exc()

# Restore original method
ExcelImporter.import_data = original_import_data