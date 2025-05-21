# Excel Import - Otomatik Kategori Oluşturma Sistemi

## Genel Bakış

VivaCRM v2'de Excel üzerinden ürün içe aktarma sırasında kategoriler otomatik olarak eşleştirilir ve gerekirse yeni kategoriler oluşturulur.

## Çalışma Mantığı

### 1. Kategori Eşleştirme
- Excel'deki kategori adı önce mevcut kategorilerle karşılaştırılır
- Case-insensitive (büyük/küçük harf duyarsız) arama yapılır
- Tam eşleşme bulunursa o kategori kullanılır

### 2. Benzer Kategori Önerisi
- Tam eşleşme bulunamazsa, benzer kategoriler aranır
- SequenceMatcher algoritması ile benzerlik skorları hesaplanır
- %85 ve üzeri benzerlik skoru olan kategoriler otomatik eşleştirilir
- %85 altındaki benzerlikler kullanıcıya öneri olarak sunulur

### 3. Otomatik Kategori Oluşturma
- Hiç eşleşme bulunamazsa veya benzerlik skoru düşükse
- Yeni kategori otomatik olarak oluşturulur
- Kategori açıklamasına "Excel import'tan otomatik oluşturuldu" notu eklenir
- Oluşturulan kategori aktif olarak işaretlenir

## Kod Değişiklikleri

### 1. `core/excel_corrections.py`
```python
def correct_category(self, value: Any, create_if_not_exists: bool = True) -> Tuple[Optional[str], bool]:
    # ... kategori kontrolü
    if create_if_not_exists:
        new_category = Category.objects.create(
            name=value_str,
            slug=slugify(value_str),
            description=f"Excel import'tan otomatik oluşturuldu - {datetime.now()}",
            is_active=True
        )
```

### 2. `products/views_excel.py`
```python
# Import sırasında otomatik kategori oluşturma
existing_category = Category.objects.filter(name__iexact=category_name).first()
if existing_category:
    category = existing_category
else:
    # Yoksa yeni oluştur
    category = Category.objects.create(
        name=category_name,
        slug=slugify(category_name),
        description=f"Excel import'tan otomatik oluşturuldu",
        is_active=True
    )
```

## Kullanıcı Arayüzü

### Hata Düzeltme Sayfası
- Kategori bulunamadı hataları "Otomatik Oluşturulacak" notu ile gösterilir
- Kullanıcıya bilgi mesajı: "Sistemde bulunmayan kategoriler otomatik olarak oluşturulacaktır"
- Manuel düzeltme seçeneği korunur

### Otomatik Düzeltme Seçenekleri
- "Kategori Eşleştirme ve Oluşturma" seçeneği
- Benzer kategorileri bulur veya yeni kategori oluşturur

## Avantajlar

1. **Zaman Tasarrufu**: Manuel kategori oluşturma gerekmez
2. **Tutarlılık**: Benzer kategoriler otomatik eşleştirilir
3. **Hata Azaltma**: Kategori eksikliği hataları engellenir
4. **Esneklik**: Manuel düzeltme seçeneği korunur

## Güvenlik ve Performans

- Kategori oluşturma işlemleri transaction içinde yapılır
- Cache mekanizması ile tekrarlayan sorgular engellenir
- Slug'lar otomatik ve benzersiz olarak oluşturulur

## Kullanım Örnekleri

### Örnek 1: Tam Eşleşme
- Excel: "Elektronik"
- Sistem: Mevcut "Elektronik" kategorisi kullanılır

### Örnek 2: Benzer Eşleşme
- Excel: "Elektonik" (yazım hatası)
- Sistem: "Elektronik" kategorisi önerilir (%90 benzerlik)

### Örnek 3: Yeni Kategori
- Excel: "Akıllı Ev Sistemleri"
- Sistem: Yeni kategori otomatik oluşturulur