# VivaCRM v2 Teknoloji Güncellemeleri ve Versiyonları

Bu dokümanda, VivaCRM v2 projesinde kullanılan teknolojilerin en güncel versiyonları ve yeni özellikleri detaylandırılmıştır.

## 1. Backend Teknolojileri

### Django 5.1 (En Son Versiyon)
- **Minimum Python Versiyonu**: Python 3.10, 3.11, 3.12, ve 3.13
- **Yeni Özellikler**:
  - `{% querystring %}` template tag eklendi - URL parametrelerini kolayca yönetme
  - DomainNameValidator ile domain doğrulama
  - Performans iyileştirmeleri
  - SQL/JSON yetenekleri - JSON verileri tablo görünümüne dönüştürme
  - Logical replication geliştirmeleri
  - Gelişmiş monitoring ve analiz özellikleri
- **En Son Güncelleme**: Django 5.1.7 (güvenlik güncellemeleri dahil)
- **Dikkat**: Django 5.2 LTS (Uzun Süreli Destek) olarak belirlendi

### Django Admin Panel
- Django 5.1 ile gelen yenilikler:
  - Geliştirilmiş arama özellikleri
  - Modern UI/UX iyileştirmeleri
  - Performans optimizasyonları
  - Responsive design iyileştirmeleri

## 2. Frontend Teknolojileri

### HTMX 2.0.4 (En Son Versiyon)
- **Çıkış Tarihi**: Haziran 17, 2024
- **Yeni Özellikler**:
  - Extension yönetiminde değişiklikler (ayrı repo: https://extensions.htmx.org)
  - Web Components desteği - Shadow DOM içinde çalışabilme
  - HTTP standartlarına uyumluluk (DELETE request'lerde query parameters)
  - Head tag birleştirme özelliği dahili olarak eklendi
  - Konfigürasyon seçenekleri genişletildi
- **Kurulum**: `<script src="https://unpkg.com/htmx.org@2.0.4"></script>`

### Alpine.js 3.14.9 (En Son Versiyon)
- **Temel Özellikler**:
  - 15 directive, 6 property, 2 method
  - Minimalist ve modern yaklaşım
  - x-data, x-on, x-text, x-show gibi temel directive'ler
- **Kurulum**: `<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.9/dist/cdn.min.js"></script>`
- **Son Güncelleme**: 2 ay önce

### TailwindCSS 3.x + daisyUI 5.0
- **daisyUI 5.0 Yeni Özellikler**:
  - Geliştirilmiş renk sistemi - CSS değişkenleri içinde tam renk desteği
  - Calendar/Datepicker desteği (Cally, Pikaday, React Day Picker)
  - Form doğrulama desteği - Validator sınıfı
  - Yeni Dock komponenti - mobil uyumlu navigasyon barı
  - Component iyileştirmeleri - Alert'te soft/dash stiller
- **Breaking Changes**:
  - Menu component değişiklikleri
  - Select component varsayılan genişlik güncellendi
  - Bazı mask utility'ler kaldırıldı

## 3. Veritabanı ve Cache

### PostgreSQL 17 (En Son Versiyon)
- **Çıkış Tarihi**: 26 Eylül 2024
- **Yeni Özellikler**:
  - Yeni bellek yönetimi sistemi - VACUUM için 20x daha az bellek kullanımı
  - Geliştirilmiş sorgu performansı
  - SQL/JSON yetenekleri - JSON_TABLE() fonksiyonu
  - Logical replication geliştirmeleri - failover slot desteği
  - Gelişmiş monitoring - pg_wait_events sistem görünümü
- **En Son Versiyon**: PostgreSQL 17.5

### Redis 8.0 (En Son Versiyon)
- **Yeni Özellikler**:
  - 30+ performans iyileştirmesi
  - %5.4 - %87.4 arası gecikme azaltımı
  - %100 daha fazla throughput
  - JSON veri yapısı - JSONPath desteği
  - Time series veri yapısı
  - Vector set veri yapısı (beta)
  - Entegre modüller: Redis Query Engine, RedisJSON, RedisTimeSeries
  - Yeni komutlar: HGETDEL, HGETEX, HSETEX
- **Lisans Seçenekleri**: RSALv2, SSPLv1, AGPLv3

## 4. Asenkron İşlem ve API

### Celery 5.4 (En Son Versiyon)
- **Python Desteği**: Python 3.8, 3.9, 3.10
- **Yeni Özellikler**:
  - Django transaction desteği - delay_on_commit() API
  - Kombu 5.3 minimum versiyon
  - redis-py 4.5.x minimum versiyon
  - SQLAlchemy 1.4.x & 2.0.x desteği
  - zoneinfo ile timezone yönetimi (pytz yerine)
- **Odak**: Stabilite ve güvenilirlik iyileştirmeleri

### Django REST Framework 3.15 (En Son Versiyon)
- **Çıkış Tarihi**: 15 Mart 2024
- **Django Desteği**: Django 5.0 tam destek
- **Python Desteği**: Python 3.12 tam destek
- **Yeni Özellikler**:
  - UniqueConstraint desteği - ModelSerializer'da validator'lar
  - SimpleRouter geliştirmeleri - use_regex_path argümanı
  - Timezone desteği - pytz'den ZoneInfo'ya geçiş
  - Arama iyileştirmeleri - tırnak içinde phrase arama
- **Not**: 3.15.2'de büyük breaking change'ler var

## 5. Ek Teknolojiler

### Django Channels 4.2
- **Özellikler**:
  - WebSocket communication
  - Real-time chat uygulamaları
  - IoT protokol desteği
  - Senkron ve asenkron bağlantı stilleri
  - ASGI tabanlı mimari

### Elasticsearch 8.17
- **Yeni Özellikler**:
  - Enterprise-exclusive synthetic _source özelliği
  - Logs data streams (logsdb index mode)
  - Time series data streams desteği
  - APM ve Universal Profiling iyileştirmeleri
  - Güvenlik yamaları

### Docker 27 (En Son Versiyon)
- **Docker 27.5 Özellikleri**:
  - Default bridge başlatma sorunu düzeltmesi
  - DOCKER_IGNORE_BR_NETFILTER_ERROR environment değişkeni
- **Docker 27.4 Özellikleri**:
  - OTel yapılandırılmadığında bellek tahsis sorunu düzeltmesi
  - Kernel modül yükleme iyileştirmeleri
- **Entegrasyonlar**:
  - Buildx v0.15.1
  - BuildKit v0.14.1
  - Compose v2.28.1

## Öneriler ve Dikkat Edilmesi Gerekenler

1. **Django 5.1'e Geçiş**: Python 3.8 desteği kaldırıldı, minimum Python 3.10 gerekiyor
2. **HTMX 2.0**: Extension'lar artık ayrı yüklenmeli
3. **daisyUI 5.0**: Breaking change'lere dikkat edilmeli
4. **PostgreSQL 17**: Performans kazanımları için VACUUM ayarlarını güncelleme
5. **Redis 8.0**: Yeni veri yapılarını değerlendirme
6. **Celery 5.4**: Django transaction desteğinden yararlanma
7. **Django REST Framework 3.15**: Python ve Django versiyon gereksinimleri

## Versiyon Uyumluluk Tablosu

| Teknoloji | Minimum Python | Minimum Django |
|-----------|---------------|----------------|
| Django 5.1 | 3.10 | - |
| Django REST Framework 3.15 | 3.6 | 3.0 |
| Celery 5.4 | 3.8 | 2.2.28 |
| Django Channels 4.2 | 3.7 | 3.2 |

Bu belge, proje teknolojilerinin güncel tutulması ve gelecek güncellemelerin planlanması için referans olarak kullanılabilir.