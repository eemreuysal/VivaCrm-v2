import pandas as pd

# Create test Excel file with template column names
def create_test_excel_with_template_columns():
    """Create a test Excel file with column names matching the template"""
    
    # Use column names from the template
    data = {
        'SKU': ['TEST001', 'TEST002', 'TEST003'],
        'URUNISMI': ['Test Ürün 1', 'Test Ürün 2', 'Test Ürün 3'],
        'FIYAT': [100.50, 200.00, 150.75],
        'STOK': [50, 100, 75],
        'KATEGORI': ['Elektronik', 'Giyim', 'Kitap'],
        'AÇIKLAMA': ['Test açıklama 1', 'Test açıklama 2', 'Test açıklama 3']
    }
    
    df = pd.DataFrame(data)
    file_path = 'test_product_template.xlsx'
    df.to_excel(file_path, index=False)
    print(f"Created test file: {file_path}")
    print("Columns:", df.columns.tolist())
    return file_path

# Create test Excel file with legacy column names
def create_test_excel_with_legacy_columns():
    """Create a test Excel file with legacy column names"""
    
    data = {
        'sku': ['LEGACY001', 'LEGACY002'],
        'Ürün Adı': ['Legacy Ürün 1', 'Legacy Ürün 2'],
        'Fiyat': [300.00, 400.00],
        'Stok Miktarı': [25, 30],
        'Kategori': ['Mobilya', 'Elektronik'],
        'Açıklama': ['Legacy açıklama 1', 'Legacy açıklama 2']
    }
    
    df = pd.DataFrame(data)
    file_path = 'test_product_legacy.xlsx'
    df.to_excel(file_path, index=False)
    print(f"Created test file: {file_path}")
    print("Columns:", df.columns.tolist())
    return file_path

# Create test Excel file with mixed case columns
def create_test_excel_with_mixed_case():
    """Create a test Excel file with mixed case column names"""
    
    data = {
        'Sku': ['MIXED001', 'MIXED002'],
        'urunismi': ['Mixed Ürün 1', 'Mixed Ürün 2'],
        'FiYaT': [500.00, 600.00],
        'STOK': [15, 20],
        'kategori': ['Oyuncak', 'Spor'],
        'AÇIKLAMA': ['Mixed açıklama 1', 'Mixed açıklama 2']
    }
    
    df = pd.DataFrame(data)
    file_path = 'test_product_mixed_case.xlsx'
    df.to_excel(file_path, index=False)
    print(f"Created test file: {file_path}")
    print("Columns:", df.columns.tolist())
    return file_path

# Test column mapping function (similar to what's in views_excel.py)
def test_column_mapping(file_path):
    """Test the column mapping logic"""
    print(f"\nTesting column mapping for: {file_path}")
    
    df = pd.read_excel(file_path)
    print("Original columns:", df.columns.tolist())
    
    # Normalize column names - case insensitive mapping
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
            # Keep original column name if no mapping found
            normalized_columns[col] = col_lower
    
    # Rename columns
    df = df.rename(columns=normalized_columns)
    print("Normalized columns:", df.columns.tolist())
    
    # Check for required columns
    required_columns = ['name', 'price']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
    else:
        print("SUCCESS: All required columns found!")
        print(f"  - Name column values: {df['name'].tolist()}")
        print(f"  - Price column values: {df['price'].tolist()}")

if __name__ == "__main__":
    print("Product Import Column Mapping Test")
    print("=" * 40)
    
    # Create and test different Excel formats
    test_files = []
    
    print("\n1. Creating test Excel with template columns...")
    test_files.append(create_test_excel_with_template_columns())
    
    print("\n2. Creating test Excel with legacy columns...")
    test_files.append(create_test_excel_with_legacy_columns())
    
    print("\n3. Creating test Excel with mixed case columns...")
    test_files.append(create_test_excel_with_mixed_case())
    
    # Test column mapping for each file
    print("\n" + "=" * 40)
    print("Testing Column Mapping")
    print("=" * 40)
    
    for file_path in test_files:
        test_column_mapping(file_path)
        print("-" * 40)