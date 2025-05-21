import pandas as pd

# Test için bir örnek Excel dosyası oluştur
file_path = "test_order_import.xlsx"

# Örnek veri
data = {
    'customer_email': ['test1@example.com', 'test2@example.com'],
    'product_sku': ['TEST001', 'TEST001'], 
    'quantity': [5, 10],
    'unit_price': [150.00, 150.00]
}

# DataFrame oluştur ve Excel'e kaydet
df = pd.DataFrame(data)
df.to_excel(file_path, index=False)

print("Excel dosyası oluşturuldu:", file_path)

# Dosyayı oku ve kontrol et
df_check = pd.read_excel(file_path)
print("\nDosya içeriği:")
print(df_check)
print("\nSütunlar:", df_check.columns.tolist())