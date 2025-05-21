#!/usr/bin/env python
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.views_excel import validate_excel_columns
import pandas as pd

def test_validate_excel_columns():
    """Test the actual validate_excel_columns function from views_excel.py"""
    
    test_files = ['test_product_template.xlsx', 'test_product_legacy.xlsx', 'test_product_mixed_case.xlsx']
    
    print("Testing validate_excel_columns function")
    print("=" * 40)
    
    for file_path in test_files:
        print(f"\nTesting: {file_path}")
        try:
            df = pd.read_excel(file_path)
            print(f"Original columns: {df.columns.tolist()}")
            
            errors = validate_excel_columns(df)
            
            if errors:
                print(f"ERROR: {errors}")
            else:
                print("SUCCESS: Validation passed!")
                # Show the normalized columns
                normalized_columns = {}
                for col in df.columns:
                    col_upper = col.upper()
                    col_lower = col.lower()
                    
                    if col_upper == 'SKU' or col_lower == 'sku':
                        normalized_columns[col] = 'sku'
                    elif col_upper == 'URUNISMI' or col_upper == 'ÜRÜN ADI':
                        normalized_columns[col] = 'name'
                    elif col_upper == 'FIYAT' or col_lower == 'fiyat':
                        normalized_columns[col] = 'price'
                    elif col_upper == 'STOK' or col_upper == 'STOK MIKTARI':
                        normalized_columns[col] = 'stock_quantity'
                    elif col_upper == 'AÇIKLAMA' or col_lower == 'açıklama':
                        normalized_columns[col] = 'description'
                    elif col_upper == 'KATEGORI' or col_lower == 'kategori':
                        normalized_columns[col] = 'category'
                    else:
                        normalized_columns[col] = col_lower
                
                df_normalized = df.rename(columns=normalized_columns)
                print(f"Normalized columns: {df_normalized.columns.tolist()}")
        except Exception as e:
            print(f"Exception: {e}")
        print("-" * 40)

if __name__ == "__main__":
    test_validate_excel_columns()