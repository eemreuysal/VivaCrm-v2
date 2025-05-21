import pandas as pd

# Create test data with missing categories
test_data = {
    'Ürün Kodu': ['TEST001', 'TEST002', 'TEST003'],
    'Ürün Adı': ['Test Ürün 1', 'Test Ürün 2', 'Test Ürün 3'],
    'Kategori': ['Yeni Kategori 1', 'Yeni Kategori 2', 'Elektronik'],  # First two categories don't exist
    'Fiyat': [100.50, 200.99, 150.00],
    'Stok': [50, 30, 0],
    'Açıklama': ['Test açıklama 1', 'Test açıklama 2', 'Test açıklama 3']
}

df = pd.DataFrame(test_data)
df.to_excel('/Users/emreuysal/Documents/Project/VivaCrm v2/test_product_import_with_categories.xlsx', index=False)
print("Test Excel file created successfully!")