import pandas as pd

df = pd.DataFrame({
    'customer_email': ['test@example.com', 'test2@example.com'],
    'product_sku': ['SKU001', 'SKU002'],
    'quantity': [1, 2]
})

df.to_excel('/Users/emreuysal/Documents/Project/VivaCrm v2/test_excel_file.xlsx', index=False)
print("Excel dosyası oluşturuldu: test_excel_file.xlsx")