#!/usr/bin/env python
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def trace_category_issue():
    """Trace the category validation issue"""
    
    from products.models import Product, Category
    from core.excel import ExcelImporter
    import pandas as pd
    from io import BytesIO
    
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
    
    # Verify category exists
    cat = Category.objects.filter(name='Waffle Towel').first()
    print(f"\nCategory 'Waffle Towel' exists: {cat is not None}")
    if cat:
        print(f"Category ID: {cat.id}, Name: {cat.name}")
    
    # Check Product model field
    category_field = Product._meta.get_field('category')
    print(f"\nProduct.category field type: {category_field.__class__.__name__}")
    print(f"  related_model: {category_field.related_model}")
    print(f"  null: {category_field.null}, blank: {category_field.blank}")
    
    # Test field validation directly
    from django.core.exceptions import ValidationError
    
    print("\nDirect field validation test:")
    print(f"  Category object: {cat}")
    print(f"  Category type: {type(cat)}")
    
    try:
        # Clean with category object
        category_field.clean(cat, None)
        print("  ✓ Validation with Category object passed")
    except ValidationError as e:
        print(f"  ✗ Validation with Category object failed: {e}")
    
    try:
        # Clean with category ID
        category_field.clean(cat.id, None)
        print("  ✓ Validation with Category ID passed")
    except ValidationError as e:
        print(f"  ✗ Validation with Category ID failed: {e}")
    
    # Now test the actual import process
    print("\n" + "="*50)
    print("Testing actual import:")
    print("="*50)
    
    from products.excel import import_products_excel
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    
    excel_buffer.seek(0)
    try:
        result = import_products_excel(excel_buffer, user=user)
        print(f"Success: {result.success}, Failed: {result.failed}")
        print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_category_issue()