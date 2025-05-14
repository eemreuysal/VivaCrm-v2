# VivaCRM v2 İzleme ve Loglama Kılavuzu

Bu belgede, VivaCRM v2 uygulaması için izleme ve loglama stratejileri açıklanmaktadır.

## İzleme Araçları

VivaCRM v2, aşağıdaki izleme ve loglama araçlarını kullanır:

### 1. Sentry - Hata Takibi

[Sentry](https://sentry.io/), üretim ortamında oluşan hataları yakalamak, gruplamak ve bildirmek için kullanılır.

**Yapılandırma:**
- `settings.py` dosyasında Sentry entegrasyonu
- Django, Redis ve Celery entegrasyonları
- Kullanıcı bilgilerini hatalara eklemek için PII ayarı
- Farklı ortamlar için ortam tanımlayıcı (development, staging, production)

**Kullanım:**
```python
# Özel bir hatayı manuel olarak Sentry'e göndermek
import sentry_sdk

try:
    # Hata oluşturabilecek kod
    calculate_complex_function()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

### 2. Elastic APM - Performans İzleme

[Elastic APM](https://www.elastic.co/apm), uygulamanın performansını izlemek için kullanılır.

**Yapılandırma:**
- `settings.py` dosyasında Elastic APM ayarları
- Django, PostgreSQL, Redis, Celery entegrasyonları

**İzlenen Metrikler:**
- Sayfa yüklenme süreleri
- API endpoint performansı
- Veritabanı sorgu süreleri
- Önbellek kullanımı
- Celery görev süreleri

### 3. Prometheus - Metrikler

[Prometheus](https://prometheus.io/), uygulama metriklerini toplamak için kullanılır.

**Yapılandırma:**
- `django-prometheus` uygulaması
- Prometheus middleware'leri
- Özel metrikler

**Standart Metrikler:**
- HTTP istek sayısı ve süreleri
- Veritabanı sorgu sayısı
- Model işlem sayısı (oluşturma, güncelleme, silme)
- Kullanıcı işlemleri

**Özel Metrikler:**
- İş mantığına özgü metrikler (sipariş sayısı, müşteri kaydı, vb.)
- Önbellek isabet oranı
- Asenkron görev sayısı ve süreleri

### 4. Sağlık Kontrolleri

[django-health-check](https://github.com/KristianOellegaard/django-health-check), uygulamanın ve bağımlılıklarının sağlığını kontrol etmek için kullanılır.

**Kontrol Edilen Bileşenler:**
- Veritabanı bağlantısı
- Redis bağlantısı
- Celery çalışma durumu
- Depolama erişimi
- Özel iş mantığı kontrolleri

**Kontrol Noktası:**
- `/health/` URL'i üzerinden erişilebilir
- JSON veya HTML biçiminde sonuçlar
- Prometheus metriklerine entegre

## Loglama Stratejisi

VivaCRM v2, kapsamlı bir loglama stratejisi uygular:

### 1. Log Seviyeleri

- **DEBUG**: Geliştirme ve sorun giderme için detaylı bilgiler
- **INFO**: Normal sistem işlemleri (kullanıcı girişleri, işlem başlangıçları, bitişleri)
- **WARNING**: Dikkat edilmesi gereken durumlar (yavaş sorgular, önbellek kayıpları)
- **ERROR**: Sistem hataları, istisnaları
- **CRITICAL**: Kritik hatalar, acil müdahale gerektirenler

### 2. Log Hedefleri

- **Konsol**: Geliştirme ortamında
- **Dosya**: Tüm ortamlarda, farklı log tipleri için farklı dosyalar
- **Sentry**: Hatalar ve kritik uyarılar
- **Elastic Stack**: Tüm loglar, analiz için

### 3. Log Formatları

- **Geliştirme**: İnsan tarafından okunabilir format
- **Üretim**: JSON formatı (Elastic Stack, Kibana için)
- **Güvenlik**: JSON formatında yapılandırılmış, tam tarih/saat bilgisi

### 4. İzlenebilirlik

Her istek için benzersiz bir Trace ID kullanılır:
- Tüm log kayıtlarına eklenir
- HTTP yanıt başlıklarında gönderilir
- Servisler arası izleme için tutarlı olarak kullanılır

## Yapılandırma

### Django Settings

Settings dosyasında loglama ve izleme yapılandırması:

```python
# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {...},
        'json': {...},
    },
    'filters': {...},
    'handlers': {...},
    'loggers': {...},
}

# Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
# Elastic APM
ELASTIC_APM = {...}
```

### Docker Compose

Monitoring ve loglama için Docker Compose yapılandırması:

```yaml
# docker-compose.monitoring.yml
version: '3.9'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
      
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
      
  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
      
  filebeat:
    image: docker.elastic.co/beats/filebeat:7.15.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
      - ./logs:/logs
    depends_on:
      - elasticsearch

volumes:
  prometheus_data:
  grafana_data:
  elasticsearch_data:
```

## Dashboard'lar

### Grafana Dashboards

- **Sistem Dashboard**: CPU, bellek, disk kullanımı
- **Uygulama Dashboard**: İstek sayısı, yanıt süreleri, hata oranları
- **İş Mantığı Dashboard**: Sipariş sayısı, müşteri kaydı, toplam satış

### Kibana Dashboards

- **Log Analizi**: Hata oranları, log trendi
- **Güvenlik**: Şüpheli işlemler, başarısız giriş denemeleri
- **Performans**: Yavaş sorgular, API endpoint performansı

## Alarmlar ve Bildirimler

### Kritik Alarmlar

- Servis kesintileri
- Yüksek hata oranları
- Düşük disk alanı
- Veritabanı bağlantı sorunları

### Bildirim Kanalları

- Email
- Slack
- SMS
- PagerDuty

## Log Saklama ve Rotasyon

- Günlük log rotasyonu
- 14 günlük dosya saklaması
- Sıkıştırılmış arşivleme
- Amazon S3 / Google Cloud Storage'a uzun süreli saklama

## İzleme İş Akışları

### 1. Günlük İzleme

1. Grafana dashboard'ları kontrol edin
2. Sentry'de yeni hataları inceleyin
3. Kibana'da log anormallikleri arayın

### 2. Olay Yanıtı

1. Alarm bildirimi alındığında
2. Grafana/Kibana üzerinden detayları inceleyin
3. İlgili logları kontrol edin
4. Düzeltici önlemleri uygulayın
5. Olayı belgelendirin

### 3. Periyodik Analiz

1. Haftalık performans trendlerini analiz edin
2. Tekrarlayan hata desenlerini belirleyin
3. Yavaşlayan endpoint'leri tespit edin
4. Optimizasyon önerileri hazırlayın

## Ortam Spesifik Yapılandırma

### Geliştirme Ortamı
- Detaylı konsolda loglama
- DEBUG modunda çalışma
- Local dosya logları
- Docker Compose ile basit monitoring

### Test/Staging Ortamı
- JSON formatında loglama
- Sentry ve Elastic APM entegrasyonu
- Tam monitoring stack
- Daha az hassas alarmlar

### Üretim Ortamı
- Optimize edilmiş loglama seviyeleri
- Sentry ve Elastic APM tam yapılandırma
- Tam monitoring stack
- Hassas ve çok kanallı alarmlar

## Dağıtılmış İzleme

Servisler arası izleme için:
1. Trace ID'leri tüm servislerde tutarlı olarak kullanılır
2. Elastic APM ile distributed tracing yapılandırması
3. Servisler arası çağrılarda header'lar korunur

## Ekler

### Örnek Loglar

**Bilgi Logu**:
```json
{
  "time": "2024-05-14T10:15:23.123Z",
  "level": "INFO",
  "message": "Kullanıcı girişi başarılı",
  "module": "accounts.views",
  "trace_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
}
```

**Hata Logu**:
```json
{
  "time": "2024-05-14T10:15:23.123Z",
  "level": "ERROR",
  "message": "Siparişi oluşturma hatası: Yetersiz envanter",
  "module": "orders.services",
  "trace_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "exception": "ValueError: Product with ID 123 has insufficient stock",
  "stack_trace": "..."
}
```

### Yararlı Komutlar

```bash
# Log dosyalarını görüntüle
tail -f logs/vivacrm.log

# Elastic Stack statüsünü kontrol et
curl -XGET 'localhost:9200/_cluster/health?pretty'

# Prometheus metriklerini görüntüle
curl -XGET 'localhost:8000/metrics'
```