import pandas as pd
import json

# Excel dosyasını oku - tüm satırları göster
excel_file = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
df = pd.read_excel(excel_file, nrows=5)  # İlk 5 satır

print("Excel Kolon İsimleri:")
print(list(df.columns))
print("\n")

print("İlk 5 satır (tüm kolonlar):")
for idx, row in df.iterrows():
    print(f"\n--- Satır {idx+2} ---")
    for col in df.columns:
        value = row[col]
        print(f"{col}: {value} (type: {type(value).__name__})")

# Özellikle problemli görünen alanları kontrol et
print("\n\nDetaylı URUNAILESI kontrolü:")
for idx, row in df.iterrows():
    family = row['URUNAILESI']
    print(f"Row {idx+2}: '{family}' (repr: {repr(family)})")

# SKU kontrolü
print("\n\nDetaylı SKU kontrolü:")
for idx, row in df.iterrows():
    sku = row['SKU']
    print(f"Row {idx+2}: '{sku}' (repr: {repr(sku)})")

# URUNMALIYETI kontrolü  
print("\n\nDetaylı URUNMALIYETI kontrolü:")
for idx, row in df.iterrows():
    cost = row['URUNMALIYETI']
    print(f"Row {idx+2}: '{cost}' (type: {type(cost).__name__}, repr: {repr(cost)})")