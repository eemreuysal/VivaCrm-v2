import pandas as pd

# Excel dosyasını oku
excel_file = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
df = pd.read_excel(excel_file)

# İlk 20 satırdaki fiyatları kontrol et
print("Excel'deki fiyatlar (ilk 20 satır):")
for idx, row in df.head(20).iterrows():
    price = row['FIYAT']
    print(f"Row {idx+2}: Price = {price} (type: {type(price)}, repr: {repr(price)})")