import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.excel_smart_import import import_products_smart
from django.contrib.auth import get_user_model
from products.models import Product, Category, ProductFamily

User = get_user_model()

# Get admin user
admin_user = User.objects.get(username='admin')

# Excel file to import
excel_file = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'

print(f"Starting import from: {excel_file}")
print("-" * 50)

# Clear existing data for clean test
print("Clearing existing data...")
Product.objects.all().delete()
Category.objects.all().delete()
ProductFamily.objects.all().delete()
print("Data cleared.\n")

# Import products
result = import_products_smart(
    file_path=excel_file,
    user=admin_user,
    show_warnings=False  # No warnings as requested
)

# Show results
print(f"Import completed!")
print(f"Success: {result['success']}")
print("\nStatistics:")
for key, value in result['stats'].items():
    print(f"  {key}: {value}")

if result['errors']:
    print(f"\nErrors ({len(result['errors'])} total):")
    # Show only first 10 errors
    for error in result['errors'][:10]:
        print(f"  - {error}")
    if len(result['errors']) > 10:
        print(f"  ... and {len(result['errors']) - 10} more errors")

if result['created_categories']:
    print(f"\nCreated {len(result['created_categories'])} categories:")
    for cat in result['created_categories']:
        print(f"  - {cat.name}")

if result['created_families']:
    print(f"\nCreated {len(result['created_families'])} product families:")
    # Show only first 5 families
    for fam in result['created_families'][:5]:
        print(f"  - {fam.name}")
    if len(result['created_families']) > 5:
        print(f"  ... and {len(result['created_families']) - 5} more families")

print(f"\nCreated {len(result['created_products'])} products")
print(f"Updated {len(result['updated_products'])} products")

# Show sample of created products
if result['created_products']:
    print("\nSample of created products:")
    for product in result['created_products'][:5]:
        print(f"  - {product.code}: {product.name}")
        print(f"    Price: {product.price}, Category: {product.category.name}")
        print(f"    SKU: {product.sku}, ASIN: {product.asin}")
        print(f"    Family: {product.family.name if product.family else 'None'}")
        print()

# Verify price precision
print("\nPrice precision check:")
sample_products = Product.objects.all()[:10]
for product in sample_products:
    print(f"  {product.code}: Price = {product.price} (decimals: {str(product.price).split('.')[-1] if '.' in str(product.price) else '0'})")

print("-" * 50)
print("Import test completed!")