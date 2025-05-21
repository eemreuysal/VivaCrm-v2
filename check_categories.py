import pandas as pd
from products.models import Category

# Excel dosyasını oku
filename = input("Excel dosyasının adını girin (örn: products.xlsx): ")
df = pd.read_excel(filename)

# Kategori sütunu isimlerini kontrol et
print("Excel sütun isimleri:")
print(df.columns.tolist())

# Kategori sütununu bul
category_columns = [col for col in df.columns if 'category' in col.lower() or 'kategori' in col.lower()]
print(f"\nBulunan kategori sütunları: {category_columns}")

if category_columns:
    category_column = category_columns[0]
    excel_categories = df[category_column].unique()
    
    print(f"\nExcel'deki kategori değerleri:")
    for cat in excel_categories:
        print(f"'{cat}' (Tipi: {type(cat)})")
    
    print("\nVeritabanındaki kategoriler:")
    for cat in Category.objects.all():
        print(f"'{cat.name}' (ID: {cat.id})")
    
    # Eşleşmeyen kategorileri bul
    print("\nEşleşmeyen kategoriler:")
    for excel_cat in excel_categories:
        if pd.notna(excel_cat):  # NaN değerleri atla
            exists = Category.objects.filter(name__iexact=str(excel_cat).strip()).exists()
            if not exists:
                print(f"Excel: '{excel_cat}' - Veritabanında YOK")
            else:
                cat = Category.objects.get(name__iexact=str(excel_cat).strip())
                print(f"Excel: '{excel_cat}' - DB: '{cat.name}' (ID: {cat.id})")
else:
    print("Kategori sütunu bulunamadı!")