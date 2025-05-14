# VivaCRM v2 CI/CD Pipeline

Bu belge, VivaCRM v2 projesi için Sürekli Entegrasyon (CI) ve Sürekli Dağıtım (CD) süreçlerini açıklar.

## CI/CD İş Akışı

VivaCRM v2, GitHub Actions kullanarak otomatik bir CI/CD pipeline'ı çalıştırır.

### İş Akışı Bileşenleri

1. **Test**: Unit ve entegrasyon testlerinin çalıştırılması
2. **Lint**: Kod kalitesi ve biçimlendirme kontrolü
3. **Docker Build**: Docker imajının oluşturulması ve test edilmesi
4. **Deployment**: Üretim ortamına otomatik dağıtım (Prod branch'e push edildiğinde)

## Pipeline Ayrıntıları

### Test İş Akışı

- Python 3.12 ile çalışır
- PostgreSQL ve Redis servislerini başlatır
- Bağımlılıkları yükler
- Migrasyonları çalıştırır
- Unit testleri pytest ile çalıştırır
- Test coverage raporunu oluşturur ve Codecov'a yükler

### Lint İş Akışı

- Flake8 ile kod kalitesi kontrolü yapar
- Black ile kod biçimlendirme kontrolü yapar

### Docker Build İş Akışı

- Docker imajı oluşturur
- docker-compose yapılandırmalarını doğrular

### Deployment İş Akışı

- Sadece 'prod' branch'ine push yapıldığında çalışır
- Docker imajını oluşturur ve DockerHub'a yükler
- SSH üzerinden üretim sunucusuna bağlanır
- Sunucuda yeni imaj ile servisleri günceller

## Pipeline Kurulumu

### Gerekli Ortam Değişkenleri

Pipeline'ın düzgün çalışması için GitHub repository'sine aşağıdaki sırları (secrets) eklemeniz gerekir:

- `DOCKERHUB_USERNAME`: DockerHub kullanıcı adı
- `DOCKERHUB_TOKEN`: DockerHub erişim token'ı
- `PRODUCTION_HOST`: Üretim sunucusu IP adresi veya hostname
- `PRODUCTION_USERNAME`: Üretim sunucusu kullanıcı adı
- `PRODUCTION_SSH_KEY`: Üretim sunucusuna erişim için SSH private key

### GitHub Secrets Ekleme

1. GitHub repository'nizde "Settings" > "Secrets and variables" > "Actions" bölümüne gidin
2. "New repository secret" butonuna tıklayın
3. İsim ve değer çiftlerini ekleyin

## Branch Stratejisi

- `main`: Geliştirme branch'i. Pull requestler bu branch'e gönderilir.
- `prod`: Üretim branch'i. Bu branch'e yapılan push'lar üretim ortamına otomatik olarak deploy edilir.

## CI/CD Pipeline Hataları

Pipeline hatalarını çözmek için:

1. GitHub Actions sekmesinde ilgili iş akışını açın
2. Başarısız olan adımı belirleyin
3. Log çıktılarını inceleyin
4. Sorunu düzeltin ve kodu tekrar push edin

## Manuel Deployment

Bazı durumlarda manuel deployment yapmanız gerekebilir:

```bash
# DockerHub'a giriş yapın
docker login

# İmajı oluşturun ve yükleyin
docker build -t vivacrm/vivacrm:latest .
docker push vivacrm/vivacrm:latest

# Sunucuya bağlanın
ssh user@production-server

# Uygulamayı güncelleyin
cd /path/to/vivacrm
git pull
docker-compose pull
docker-compose up -d
```

## CI/CD Pipeline Özelleştirme

Özel CI/CD ihtiyaçlarınız için:

1. `.github/workflows/ci-cd.yml` dosyasını düzenleyin
2. Yeni adımlar ekleyin veya mevcut adımları değiştirin
3. Değişiklikleri commit'leyin ve push edin

---

CI/CD pipeline'ı ile ilgili sorularınız varsa, lütfen ekip yöneticinizle iletişime geçin.