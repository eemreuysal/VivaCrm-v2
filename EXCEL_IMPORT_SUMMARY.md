# VivaCRM v2 Excel Import Sistemi Özeti

Bu dokümanda oluşturulan Excel import sistemi ve WebSocket desteği açıklanmaktadır.

## Oluşturulan Dosyalar

### 1. Core İmport Modelleri
- **`core/models_import.py`**: İmport işlemlerini takip eden modeller
  - `ImportJob`: Ana import işlem modeli
  - `ImportError`: Import hataları modeli
  - `ImportHistory`: Import geçmişi modeli
  - `ImportTemplate`: Import şablonları modeli

### 2. Excel Task'ları
- **`products/tasks_excel.py`**: Ürün import task'ları
  - `product_import_task`: Ürün içe aktarım
  - `stock_adjustment_task`: Stok düzeltme
  - `import_status_task`: İşlem durumu kontrolü

- **`orders/tasks_excel.py`**: Sipariş import task'ları
  - `order_import_task`: Sipariş içe aktarım
  - `import_status_task`: İşlem durumu kontrolü

### 3. Celery Konfigürasyonu
- **`core/celery_config.py`**: Güncellendi
  - Yeni kuyruklar: `excel_import`, `excel_export`
  - Task routing ve timeout ayarları
  - Task-bazlı zaman limitleri

### 4. WebSocket Desteği

#### Konfigürasyon
- **`core/settings.py`**: Channels eklendi
- **`core/asgi.py`**: WebSocket protokolü desteği
- **`requirements.txt`**: Yeni bağımlılıklar

#### WebSocket Dosyaları
- **`core/routing.py`**: WebSocket URL yapılandırması
- **`core/consumers.py`**: WebSocket consumer'ları
  - `ImportProgressConsumer`: İmport ilerleme takibi
  - `NotificationConsumer`: Genel bildirimler
- **`core/websocket_utils.py`**: Yardımcı fonksiyonlar

### 5. Frontend Örneği
- **`templates/products/import_progress.html`**: WebSocket kullanan örnek template

### 6. Veritabanı Migration
- **`core/migrations/0001_initial_import_models.py`**: Import modelleri için migration

### 7. Admin Arayüzü
- **`core/admin.py`**: Import modelleri için admin kayıtları

## Özellikler

### Task Özellikleri
- Chunk-bazlı işleme (varsayılan 100 satır)
- İlerleme takibi
- Detaylı hata raporlama
- WebSocket ile gerçek zamanlı güncelleme
- İşlem geçmişi kayıtları

### WebSocket Özellikleri
- Gerçek zamanlı ilerleme güncellemeleri
- İşlem durumu bildirimleri
- Hata bildirimleri
- İşlem iptali desteği

### Import Özellikleri
- Excel dosyalarından veri içe aktarım
- Mevcut kayıtları güncelleme seçeneği
- Otomatik veri doğrulama
- İlişkili verileri otomatik oluşturma (müşteri, ürün vb.)
- Hata toleranslı işleme

## Kullanım

### 1. Celery Worker Başlatma
```bash
# Varsayılan kuyruk
celery -A core worker -l info

# Excel import kuyruğu
celery -A core worker -Q excel_import -l info

# Tüm kuyruklar
celery -A core worker -Q default,excel_import,excel_export -l info
```

### 2. Import İşlemi Başlatma
```python
from products.tasks_excel import product_import_task
from core.models_import import ImportJob

# Import job oluştur
import_job = ImportJob.objects.create(
    import_type='product',
    file_name='products.xlsx',
    user=request.user
)

# Task'ı başlat
result = product_import_task.delay(
    str(import_job.id),
    'path/to/excel/file.xlsx',
    {'update_existing': True}
)
```

### 3. WebSocket Bağlantısı
```javascript
const socket = new WebSocket(`ws://localhost:8000/ws/imports/${importJobId}/`);

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    // İlerleme güncellemelerini işle
};
```

## Güvenlik Notları

1. WebSocket bağlantıları kimlik doğrulaması gerektirir
2. ImportJob'lar kullanıcıya özeldir
3. Dosya yükleme boyut limitleri uygulanmalı
4. Excel dosyaları güvenlik taramasından geçirilmeli

## Performans Önerileri

1. Büyük dosyalar için chunk boyutunu ayarlayın
2. Redis cache kullanın
3. Celery worker sayısını ihtiyaca göre ölçeklendirin
4. İmport işlemlerini yoğun olmayan saatlere planlayın

## Gelecek Geliştirmeler

1. Import önizleme özelliği
2. Import şablonları yönetimi UI'si
3. Otomatik import planlama
4. Import sonuçları e-posta bildirimi
5. Batch import desteği
6. Import rollback özelliği