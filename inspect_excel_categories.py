import pandas as pd
import os
import sys
import django

# Django ayarları
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Category

# Excel dosyasını oku - tam yolu belirtin
excel_file = input("Excel dosyasının tam yolunu girin: ")

if not os.path.exists(excel_file):
    print(f"Dosya bulunamadı: {excel_file}")
    sys.exit(1)

df = pd.read_excel(excel_file)

print(f"Excel dosyası yüklendi. Toplam satır: {len(df)}")
print(f"Sütunlar: {df.columns.tolist()}")

# Kategori sütununu bul
cat_columns = []
for col in df.columns:
    col_lower = col.lower()
    if 'category' in col_lower or 'kategori' in col_lower:
        cat_columns.append(col)

print(f"\nBulunan kategori sütunları: {cat_columns}")

if cat_columns:
    cat_col = cat_columns[0]
    print(f"\nKullanılacak sütun: {cat_col}")
    
    # Benzersiz kategorileri al
    unique_categories = df[cat_col].dropna().unique()
    
    print(f"\nExcel'deki benzersiz kategori sayısı: {len(unique_categories)}")
    print("\nKategoriler:")
    for i, cat in enumerate(unique_categories[:20]):  # İlk 20 tanesini göster
        # Kategoriyi temizle
        cat_str = str(cat).strip()
        print(f"{i+1}. '{cat}' (Tip: {type(cat).__name__}, Uzunluk: {len(cat_str)})")
        
        # Karakter kontrolü
        if i < 5:  # İlk 5 tanesinin karakterlerini göster
            print(f"   Karakterler: {repr(cat)}")
        
        # Veritabanında var mı kontrol et
        exists = Category.objects.filter(name__iexact=cat_str).exists()
        print(f"   Veritabanında: {'VAR' if exists else 'YOK'}")
        
        if not exists:
            # Benzer kategorileri bul
            similar = Category.objects.filter(name__icontains=cat_str[:5])
            if similar.exists():
                print(f"   Benzer kategoriler: {[c.name for c in similar]}")
        print()
else:
    print("Kategori sütunu bulunamadı!")

# Veritabanındaki kategorileri listele
print("\nVeritabanındaki kategoriler:")
for cat in Category.objects.all():
    print(f"- '{cat.name}' (ID: {cat.id}, Slug: {cat.slug})")