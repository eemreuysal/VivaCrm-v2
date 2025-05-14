# VivaCRM v2 Güvenlik Kılavuzu

Bu belge, VivaCRM v2 uygulamasının güvenlik yaklaşımını, özellikleri ve en iyi uygulamaları açıklar.

## Güvenlik Özellikleri

### 1. Kimlik Doğrulama ve Yetkilendirme

#### Kimlik Doğrulama
- Django'nun yerleşik kimlik doğrulama sistemi
- Argon2 parola hash algoritması
- Parola gücü kontrolü
- Oturum süre sınırları
- Başarısız giriş denemesi sınırlaması

#### Yetkilendirme
- Role dayalı erişim kontrolü
- İnce taneli izin sistemi
- Nesne düzeyinde izinler
- İşlev düzeyinde erişim kontrolü

### 2. Veri Doğrulama ve Sanitizasyon

#### Giriş Doğrulama
- Form doğrulama
- API istek doğrulama
- Veri türü kontrolü
- İş kuralları doğrulama

#### Çıktı Sanitizasyonu
- HTML sanitizasyonu (Bleach ile)
- XSS koruması
- CSRF koruması
- JSON sanitizasyonu

### 3. İletişim Güvenliği

#### HTTP Güvenliği
- HTTPS gerektirme
- HTTP Güvenlik Başlıkları
  - Content-Security-Policy (CSP)
  - X-Content-Type-Options
  - X-XSS-Protection
  - X-Frame-Options
  - Referrer-Policy

#### API Güvenliği
- Token tabanlı kimlik doğrulama
- İstek hız sınırlaması
- CORS yapılandırması
- API anahtarı rotasyonu

### 4. Depolama Güvenliği

#### Veritabanı Güvenliği
- Parametreli sorgular
- En az ayrıcalık ilkesi
- Veritabanı şifreleme
- Veritabanı yedekleme ve geri yükleme

#### Dosya Depolama Güvenliği
- Yüklenen dosya doğrulama
- Dosya türü ve boyut kontrolü
- Güvenli depolama yolları
- Medya erişim kontrolü

### 5. Günlük Kaydı ve İzleme

#### Güvenlik Günlük Kaydı
- Güvenlik olayları günlük kaydı
- Erişim günlükleri
- Değişiklik günlükleri
- Oturum günlükleri

#### İzleme ve Uyarılar
- Şüpheli etkinlik algılama
- Güvenlik ihlali uyarıları
- Performans izleme
- Sistem durum izleme

## Güvenlik Kontrol Listesi

Bu kontrol listesi, uygulamanın güvenliğini sağlamak için kullanılmalıdır:

### Kimlik Doğrulama
- [x] Güçlü parola politikası uygulanıyor
- [x] Çok faktörlü kimlik doğrulama seçeneği
- [x] Geçici oturumlar (hatırla seçeneği)
- [x] Parola sıfırlama akışı güvenli
- [x] Oturum çalma koruması
- [x] Hesap kilitleme mekanizması

### Yetkilendirme
- [x] Role dayalı erişim kontrolü
- [x] İnce taneli izin sistemi
- [x] Yatak API endpoint'leri korumalı
- [x] Doğrudan nesne referansı koruması
- [x] Fonksiyon düzeyinde erişim kontrolü

### Veri Güvenliği
- [x] CSRF koruması etkin
- [x] XSS koruması etkin
- [x] SQL Injection koruması etkin
- [x] Hassas veriler şifrelenmiş
- [x] Güvenli dosya yükleme
- [x] Kişisel verileri koruma

### İletişim Güvenliği
- [x] HTTPS zorunlu
- [x] HTTP Güvenlik başlıkları
- [x] API token güvenliği
- [x] İstek hız sınırlaması
- [x] Güvenli oturum yönetimi
- [x] API anahtar rotasyonu

### Altyapı Güvenliği
- [x] Güncel bağımlılıklar
- [x] En az ayrıcalık ilkesi
- [x] Docker konteynerleri güvenliği
- [x] Güvenlik duvarı yapılandırması
- [x] Ağ bölümlendirme
- [x] Düzenli güvenlik güncellemeleri

### Günlük Kaydı ve İzleme
- [x] Güvenlik olayları günlüğü
- [x] Kullanıcı işlemleri günlüğü
- [x] Günlük dosyalarının bütünlüğü
- [x] Şüpheli etkinlik uyarıları
- [x] Günlük saklama politikası
- [x] Merkezi log yönetimi

### Veri Koruması
- [x] Veri sınıflandırma
- [x] Hassas veri keşfi
- [x] Veri saklama politikası
- [x] Veri silme yöntemleri
- [x] Veri yedeği şifreleme
- [x] İşlemsel bütünlük

## Güvenlik En İyi Uygulamaları

### Kod Güvenliği

1. **Güvenli Kodlama**
   - Girdileri her zaman doğrulayın
   - Varsayılandan güvenli ilkesini uygulayın
   - Hata mesajlarında hassas bilgi göstermeyin
   - Güvenli varsayılan ayarlar kullanın

2. **Kod İncelemesi**
   - Güvenlik odaklı kod incelemeleri yapın
   - Statik kod analizi araçları kullanın
   - Güvenlik açıklarını tarayın
   - Kod kalitesi metriklerini izleyin

3. **Bağımlılık Yönetimi**
   - Bağımlılıkları düzenli olarak güncelleyin
   - Güvenlik açığı tarayıcıları kullanın
   - Bağımlılık lisanslarını kontrol edin
   - Kullanılmayan bağımlılıkları kaldırın

### Operasyonel Güvenlik

1. **Ortam Yönetimi**
   - Geliştirme, test ve üretim ortamlarını ayırın
   - Üretim verisini test ortamlarında kullanmayın
   - Ortam değişkenlerini güvenli şekilde yönetin
   - Farklı ortamlar için farklı kimlik bilgileri kullanın

2. **Dağıtım Güvenliği**
   - Güvenli CI/CD pipeline'ı kullanın
   - Dağıtım öncesi güvenlik kontrolleri yapın
   - Dağıtılan uygulamaları imzalayın
   - Mavi-yeşil dağıtım stratejisi kullanın

3. **İzleme ve Yanıt**
   - Gerçek zamanlı güvenlik izleme
   - Olay müdahale planı oluşturma
   - Düzenli güvenlik denetimi
   - Güvenlik ihlali tatbikatları

## Güvenli Geliştirme Yaşam Döngüsü (SDLC)

1. **Planlama**
   - Güvenlik gereksinimlerini tanımlama
   - Tehdit modellemesi yapma
   - Güvenlik kontrol listesi oluşturma

2. **Tasarım**
   - Güvenli mimari tasarımı
   - Tehdit modellemesi
   - Güvenlik kontrolleri tasarımı

3. **Geliştirme**
   - Güvenli kodlama standartları
   - Kod incelemeleri
   - Geliştiricilerin güvenlik eğitimi

4. **Test**
   - Güvenlik testleri
   - Penetrasyon testleri
   - Statik ve dinamik kod analizi

5. **Dağıtım**
   - Güvenli dağıtım süreçleri
   - Dağıtım öncesi güvenlik onayı
   - Güvenlik yapılandırması kontrolü

6. **Bakım**
   - Güvenlik izleme
   - Güvenlik güncellemeleri
   - Güvenlik olaylarına yanıt verme

## Güvenlik Olayları Yanıt Planı

1. **Hazırlık**
   - Güvenlik ekibini belirleme
   - İletişim planı oluşturma
   - Güvenlik araçlarını yapılandırma

2. **Tespit**
   - Anormallik tespiti
   - Günlük analizi
   - Güvenlik uyarıları

3. **Kapsam Belirleme**
   - Etkilenen sistemleri belirleme
   - İhlal boyutunu değerlendirme
   - Saldırı vektörünü tespit etme

4. **Çözüm**
   - Sistemleri izole etme
   - Zararı sınırlama
   - Açıkları giderme

5. **Kurtarma**
   - Sistemleri yeniden yapılandırma
   - Veri geri yükleme
   - Normal operasyonlara dönme

6. **Ders Çıkarma**
   - Olay sonrası analiz
   - Güvenlik iyileştirmelerini uygulama
   - Dokümantasyonu güncelleme

## Ek Güvenlik Kaynakları

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Güvenlik Dokümantasyonu](https://docs.djangoproject.com/en/stable/topics/security/)
- [NIST Siber Güvenlik Çerçevesi](https://www.nist.gov/cyberframework)
- [GDPR Uyumluluk Kontrol Listesi](https://gdpr.eu/checklist/)

---

Bu belge VivaCRM v2 uygulamasının güvenliği için referans olarak kullanılmalıdır. Tüm geliştirici ve operasyonel ekip üyeleri bu dokümana aşina olmalı ve burada açıklanan en iyi uygulamaları uygulamalıdır.