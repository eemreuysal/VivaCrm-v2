#!/usr/bin/env python
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def find_validation_issue():
    """Search for where the second validation error is coming from"""
    
    from products.excel import import_products_excel
    import pandas as pd
    from io import BytesIO
    
    # Prepare test data
    data = {
        'Product Code *': ['SEARCH001'],
        'Product Name *': ['Search Test Product'],
        'Category': ['Waffle Towel'],
        'Price *': [100.0],
        'Initial Stock *': [50]
    }
    
    df = pd.DataFrame(data)
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    print("Test data columns:", df.columns.tolist())
    
    # Add debug prints to trace the import process
    from core.excel import ExcelImporter
    from django.core.exceptions import ValidationError
    
    # Monkey patch to add debug
    original_import_data = ExcelImporter.import_data
    
    def debug_import_data(self, file_obj, *args, **kwargs):
        print("\n=== IMPORT DATA CALLED ===")
        print(f"Required fields: {self.required_fields}")
        print(f"Field mapping: {self.field_mapping}")
        
        try:
            return original_import_data(self, file_obj, *args, **kwargs)
        except ValidationError as e:
            print(f"ValidationError caught: {e}")
            raise
    
    ExcelImporter.import_data = debug_import_data
    
    # Also patch the processrow to see what data is being extracted
    original_process_row = ExcelImporter._process_row
    
    def debug_process_row(self, row):
        print(f"\n=== PROCESS ROW ===")
        print(f"Row data: {row.to_dict()}")
        result = original_process_row(self, row)
        print(f"Processed data: {result}")
        return result
    
    ExcelImporter._process_row = debug_process_row
    
    # Now run the import
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
    
    # Restore original methods
    ExcelImporter.import_data = original_import_data
    ExcelImporter._process_row = original_process_row

if __name__ == "__main__":
    find_validation_issue()