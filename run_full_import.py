#!/usr/bin/env python3
"""
Run full product import with the updated system.
"""

import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.excel_smart_import import import_products_smart

def run_full_import():
    """Run the full product import."""
    
    # Path to the Excel file
    excel_file = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
    
    print("Running full product import...")
    print("=" * 60)
    
    # Run the import
    result = import_products_smart(
        file_path=excel_file,
        show_warnings=False  # No warnings as requested
    )
    
    # Display results
    print("\nImport Results:")
    print(f"Success: {result['success']}")
    print(f"\nStatistics:")
    for key, value in result['stats'].items():
        print(f"  {key}: {value}")
    
    if result['errors']:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(result['errors']) > 10:
            print(f"  ... and {len(result['errors']) - 10} more errors")
    
    print("\nCreated Categories:")
    for cat in result['created_categories']:
        print(f"  - {cat.name}")
    
    print("\nCreated Product Families:")
    for fam in result['created_families']:
        print(f"  - {fam.name}")
    
    print("\nFirst 5 Created Products:")
    for prod in result['created_products'][:5]:
        print(f"  - {prod.name} (SKU: {prod.sku})")
    
    print("\n" + "=" * 60)
    print("Import complete!")


if __name__ == '__main__':
    run_full_import()