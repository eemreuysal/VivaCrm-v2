#!/usr/bin/env python
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def debug_field_validation():
    """Debug field validation issues"""
    
    from products.models import Product
    from django.core.exceptions import ValidationError
    
    # Check model fields
    print("Product model fields:")
    for field in Product._meta.get_fields():
        print(f"  {field.name}: {field.__class__.__name__}")
    
    # Check which fields are required
    print("\nRequired fields in Product model:")
    for field in Product._meta.fields:
        if hasattr(field, 'null') and not field.null and not field.primary_key:
            print(f"  {field.name}: null={field.null}, blank={field.blank}")
    
    # Test field validation
    from products.models import Category
    category = Category.objects.get(name='Waffle Towel')
    
    test_data = {
        'code': 'TEST001',
        'name': 'Test Product',
        'category': category,
        'price': 100.0,
        'current_stock': 50
    }
    
    print("\nTesting field validation:")
    for field_name, value in test_data.items():
        try:
            field = Product._meta.get_field(field_name)
            print(f"  {field_name}: {field.__class__.__name__}")
            if hasattr(field, 'clean'):
                field.clean(value, None)
                print(f"    ✓ Validation passed")
        except Exception as e:
            print(f"    ✗ Validation failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_field_validation()