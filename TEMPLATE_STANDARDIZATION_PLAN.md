# Şablon Standardizasyon Planı

## 1. Mevcut Durum Analizi

### Temel Şablonlar
- `base.html`: Eski JS importları kullanıyor, doğrudan Alpine.js yükleme
- `base_unified.html`: Yeni unified JS importları kullanıyor, modüler Alpine.js
- `base_auth.html`: Kimlik doğrulama sayfaları için
- `base_dashboard.html`: Eski dashboard importları
- `base_unified_impl.html`: Unified implementasyon detayları için
- `base_dashboard_new.html`: Muhtemelen yeni dashboard şablonu
- `base_with_inline_css.html`: Inline CSS için

### Import Yapıları
- `js_includes.html`: Eski JavaScript dosyalarını ekliyor
  - Alpine.js ile ilgili kısımlar kaldırılmış
  - Tema yönetimi yok
  - Karma import yapısı

- `js_unified.html`: Yeni, modüler yapı
  - Merkezi Theme Management
  - Temiz import yapısı
  - Alpine ve HTMX entegrasyonu

### Dashboard Şablonu
- `dashboard.html` içinde inline tanımlanmış bileşenler
- Bileşenler hem global hem de Alpine.js'e kayıtlı
- Alpine-init ile çakışan manuel başlatma mekanizması
- Tema değişikliklerini farklı bir event ile dinleme

## 2. Standardizasyon Stratejisi

### Aşama 1: Base Şablonlarının Birleştirilmesi
1. `base_unified.html` temel alınacak
2. Diğer base şablonları kaldırılıp `base_unified.html`'ye inherit edilecek
3. Varsa özel ihtiyaçlar için block yapısı genişletilecek

### Aşama 2: Import Yapılarının Standardizasyonu
1. Tüm şablonlar `js_unified.html` kullanacak
2. `js_includes.html` kullanımları kaldırılacak
3. Inline script tanımlamaları `js_unified.html` içine taşınacak

### Aşama 3: Bileşen Tanımlarının Modülerleştirilmesi
1. Inline bileşen tanımları kaldırılacak
2. Tüm bileşenler `/static/js/alpine/components/` altına taşınacak
3. ES module kullanan merkezi kayıt sistemi uygulanacak

### Aşama 4: Dashboard Şablonunda Yapılacak Değişiklikler
1. Inline script tanımları kaldırılacak
2. `dashboard-components.js` modülünden import edilecek
3. Yeni tema yönetimi ve Alpine.js başlatma sistemi kullanılacak
4. Bileşen kayıtları merkezi Alpine.js index.js üzerinden gerçekleşecek

## 3. Uygulama Planı

### 3.1. Kaldırılacak veya Değiştirilecek Dosyalar
- `base.html` → `base_unified.html` ile değiştirilecek
- `base_dashboard.html` → `base_unified.html`'den inherit edecek
- `js_includes.html` → Aktif kullanımlar `js_unified.html`'ye taşınacak

### 3.2. Oluşturulacak/Güncellenecek Dosyalar
- `alpine/components/dashboard.js` → Dashboard bileşeni için
- `alpine/components/date-filter.js` → Tarih filtresi bileşeni için
- `alpine/components/orders-table.js` → Sipariş tablosu bileşeni için

### 3.3. Uygulama Adımları
1. Yeni bileşen dosyalarını oluştur ve taşı ✅
2. Base şablonları düzenle
   - `base_dashboard_unified.html` oluşturuldu ✅
3. Dashboard şablonunu güncelle ✅
   - `dashboard.html` standardize edildi ve inline scriptler kaldırıldı
4. JS include yapılarını standardize et

## 4. İlerleme Durumu

| Görev | Durum | Not |
|-------|-------|-----|
| Alpine bileşen modüllerinin oluşturulması | ✅ Tamamlandı | dashboard.js, date-filter.js, orders-table.js |
| Base dashboard unified template oluşturma | ✅ Tamamlandı | base_dashboard_unified.html |
| Dashboard şablonun güncellenmesi | ✅ Tamamlandı | Tüm inline scriptler temizlendi |
| Template yapısının dokümantasyonu | ✅ Tamamlandı | DASHBOARD_TEMPLATE_STANDARDIZATION.md |
| Tema yönetimi entegrasyonu | ✅ Tamamlandı | Grafik temaları otomatik güncelleniyor |
| Diğer şablonların güncellenmesi | 🔄 Devam Ediyor | Sıradaki şablonlar: ürün, sipariş, müşteri |
| JS includes standardizasyonu | 🔄 Devam Ediyor | js_unified.html kullanan sayfalar arttırılıyor |

## 5. Test ve Doğrulama

### 5.1. Tamamlanan Testler
1. ✅ Tema değişikliğinin çalıştığı doğrulandı
2. ✅ Alpine.js bileşenlerinin doğru yüklendiği kontrol edildi
3. ✅ HTMX entegrasyonunun sorunsuz çalıştığı doğrulandı
4. ✅ Dashboard grafiklerinin ve bileşenlerinin doğru çalıştığı doğrulandı

### 5.2. Kalan Testler
1. Farklı tarayıcılarda uyumluluk testleri
2. Mobil cihazlarda responsive tasarım testleri
3. Yüksek yük altında performans testleri

## 6. Sonraki Adımlar

1. Diğer şablonlar için aynı standardizasyon adımlarını uygula
   - Öncelik: Ürün, Sipariş ve Müşteri modüllerine ait şablonlar
2. Base şablonlarını tamamen `base_unified.html` temelli yapıya dönüştür
3. Dokümantasyonu güncellemeye devam et
4. Dashboard iyileştirmelerinden öğrenilen dersleri diğer modüllere uygula