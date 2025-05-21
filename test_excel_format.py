#!/usr/bin/env python3
"""
Test the Excel file format handling with the updated import system.
"""

import os
import sys
import django
import pandas as pd

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.excel_smart_import import SmartProductImporter

def test_excel_format():
    """Test Excel file format handling."""
    
    # Path to the Excel file
    excel_file = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
    
    print("Testing Excel format handling...")
    print("=" * 60)
    
    # First, let's check the raw data
    print("\n1. Checking raw Excel data:")
    df = pd.read_excel(excel_file, nrows=5)
    
    for index, row in df.iterrows():
        print(f"\nRow {index + 2}:")
        print(f"SKU: {repr(row.get('SKU'))}")
        print(f"URUNISMI: {repr(row.get('URUNISMI'))}")
        print(f"URUNAILESI: {repr(row.get('URUNAILESI'))}")
        print(f"URUNMALIYETI: {repr(row.get('URUNMALIYETI'))}")
        print(f"KARGOMALIYET: {repr(row.get('KARGOMALIYET'))}")
        print(f"KOMISYON: {repr(row.get('KOMISYON'))}")
    
    print("\n" + "=" * 60)
    print("\n2. Testing import system processing:")
    
    # Create a test importer
    importer = SmartProductImporter(file_path=excel_file)
    
    # Process just a few rows for testing
    df_test = pd.read_excel(excel_file, nrows=3)
    
    for index, row in df_test.iterrows():
        print(f"\nProcessing row {index + 2}:")
        
        # Test the extract method directly
        data = importer._extract_product_data(row, index + 2)
        
        if data:
            print(f"Extracted data:")
            print(f"  Code: {data.get('code')}")
            print(f"  SKU: {data.get('sku')}")
            print(f"  Name: {data.get('name')}")
            print(f"  Price: {data.get('price')} (type: {type(data.get('price'))})")
            print(f"  Cost: {data.get('cost')} (type: {type(data.get('cost'))})")
            print(f"  Category: {data.get('category')}")
            print(f"  Family: {data.get('family')}")
            
            # Check what family name was extracted
            family = row.get('URUNAILESI')
            if family and not pd.isna(family):
                print(f"\nOriginal URUNAILESI: {repr(family)}")
                # Show the cleaning process
                family_clean = str(family).strip().replace('\n', ' ').replace('\r', ' ')
                family_clean = family_clean.strip('"').strip("'")
                print(f"After cleaning: {repr(family_clean)}")
        else:
            print("No data extracted (error occurred)")
    
    print("\n" + "=" * 60)
    print("\nTesting complete!")


if __name__ == '__main__':
    test_excel_format()