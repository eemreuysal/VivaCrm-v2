import pandas as pd
import json

# Excel dosyasını oku
excel_file = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
df = pd.read_excel(excel_file)

# Kolon isimlerini göster
print("Excel Kolon İsimleri:")
print(df.columns.tolist())
print("\n")

# İlk birkaç satırı göster
print("İlk 5 satır:")
print(df.head())
print("\n")

# Kolon bilgilerini detaylı göster
print("Kolon Detayları:")
for col in df.columns:
    print(f"- {col}: {df[col].dtype}")
    
# JSON formatında da kaydet
template_info = {
    "columns": df.columns.tolist(),
    "dtypes": {col: str(df[col].dtype) for col in df.columns},
    "sample_data": df.head().to_dict('records')
}

with open('/Users/emreuysal/Documents/Project/VivaCrm v2/excel_template_info.json', 'w', encoding='utf-8') as f:
    json.dump(template_info, f, ensure_ascii=False, indent=2)