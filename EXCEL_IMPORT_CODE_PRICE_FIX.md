# Excel Import - Code ve Price Hataları Düzeltmesi

## Problem

Excel import sırasında şu hatalar alınıyordu:
- `code`: "Bu alan boş olamaz."
- `price`: "2 ondalık basamaktan daha fazla olmadığından emin olun."

## Çözüm

### 1. Code (Ürün Kodu) Otomatik Oluşturma

Product modelinde `code` alanı zorunlu (`unique=True`). Excel'de bu alan eksikse otomatik oluşturulur:

```python
# Öncelik sırası:
1. Excel'de "code" sütunu varsa kullan
2. Yoksa "sku" sütunu varsa kullan  
3. Yoksa "name" sütunundan slug oluştur
```

#### Örnek Code Oluşturma:
- Ürün Adı: "Samsung Galaxy S21"
- Oluşan Code: "SAMSUNG_GALAXY_S21"

### 2. Price (Fiyat) Formatı Düzeltmesi

Product modelinde `price` alanı 2 ondalık basamaklı (`decimal_places=2`):

```python
# Fiyat formatı düzeltmesi:
price_str = str(row['price']).replace(',', '.')  # Virgülü noktaya çevir
price = round(float(price_str), 2)  # 2 ondalığa yuvarla
```

#### Örnek Price Düzeltmesi:
- Excel: "1234,567" → Sistem: 1234.57
- Excel: "999.999" → Sistem: 1000.00

## Yapılan Değişiklikler

### 1. Field Mapping Güncellendi
```python
# Code sütunu eşleştirmeleri eklendi:
- PRODUCT CODE
- ÜRÜN KODU 
- URUNKODU
- CODE
```

### 2. Import Logic Güncellendi
```python
# Code kontrolü ve otomatik oluşturma
if 'code' not in row or pd.isna(row['code']):
    # SKU veya Name'den code oluştur
    code = generate_code_from_name_or_sku()
```

### 3. Product Oluşturma Güncellendi
```python
product_data = {
    'code': code,  # SKU yerine code kullan
    'price': round(price, 2),  # 2 ondalığa yuvarla
    # ...
}
```

## Kullanım Notları

### Excel Formatı
- Code sütunu zorunlu değil (otomatik oluşturulur)
- Price sütunu zorunlu ve sayısal olmalı
- Virgül veya nokta kullanılabilir

### Otomatik Düzeltmeler
1. Eksik code otomatik oluşturulur
2. Fiyat formatı otomatik düzeltilir
3. Slug benzersizliği sağlanır

### Hata Önleme
- Code çakışması kontrolü
- Price format kontrolü
- Slug benzersizlik kontrolü