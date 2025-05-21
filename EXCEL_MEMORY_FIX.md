# Excel Import - Bellek Aşımı Hatası Çözümü

## Problem

Excel import sırasında bellek hatası:
- `Memory usage (1191.9MB) exceeds limit (500MB)`

## Çözüm

### 1. Chunked Reading (Parça Parça Okuma)

Büyük Excel dosyaları için chunked reading sistemi eklendi:

```python
# 5MB'den büyük dosyalar için chunked processing
if file_size > 5 * 1024 * 1024:
    return self._process_large_file(file_obj, update_existing, request, file_session_id)
```

### 2. Batch Processing (Toplu İşleme)

Ürünler 50'li gruplar halinde işleniyor:

```python
batch_size = 50  # Her batch'te işlenecek ürün sayısı
if batch_counter >= batch_size:
    # Batch create/update
    Product.objects.bulk_create(products_to_create)
```

### 3. Memory Management (Bellek Yönetimi)

- Bellek sınırı: 200-300MB
- Her 25 satırda bellek kontrolü
- Garbage collection (gc.collect())

### 4. ChunkedExcelReader Sınıfı

```python
class ChunkedExcelReader:
    def __init__(self, file_path_or_buffer, chunk_size: int = 1000):
        # 1000 satırlık parçalar halinde okuma
```

## Performans İyileştirmeleri

### 1. Chunk Size Optimizasyonu
- Küçük dosyalar: Tek seferde okuma
- Orta dosyalar (5-10MB): 500 satırlık chunk'lar
- Büyük dosyalar (10MB+): 200 satırlık chunk'lar

### 2. Batch Create/Update
- bulk_create() kullanımı
- Transaction yönetimi
- Conflict handling

### 3. Bellek Temizliği
- DataFrame'leri del ile silme
- gc.collect() ile bellek temizliği
- Cache mekanizması

## Kullanım

### Küçük Dosyalar (<5MB)
- Standart işleme
- Tek seferde okuma
- Hızlı işleme

### Büyük Dosyalar (>5MB)
- Chunked reading
- Progress tracking
- Memory monitoring

## Örnek Akış

1. Dosya boyutu kontrolü
2. Uygun işleme metodunu seçme
3. Chunk'lar halinde okuma
4. Batch processing
5. Bellek temizliği
6. İlerleme takibi

## Hata Durumları

### Memory Limit Exceeded
- Chunk size küçültülür
- Garbage collection sıklaştırılır
- Batch size azaltılır

### Processing Error
- Chunk kaydedilir
- Sonraki chunk'a geçilir
- Hata loglanır

## Konfigürasyon

```python
# settings.py
EXCEL_IMPORT_CHUNK_SIZE = 200
EXCEL_IMPORT_BATCH_SIZE = 50
EXCEL_IMPORT_MEMORY_LIMIT = 300 * 1024 * 1024  # 300MB
```

## Monitoring

- Memory usage tracking
- Progress reporting
- Error logging
- Performance metrics