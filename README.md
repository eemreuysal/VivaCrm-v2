# VivaCRM v2

VivaCRM v2, modern teknolojilerle geliştirilmiş bir Müşteri İlişkileri Yönetimi (CRM) sistemidir.

## Özellikler

- Müşteri yönetimi
- Ürün ve stok yönetimi
- Sipariş takibi
- Fatura oluşturma
- Raporlama
- Kullanıcı ve yetki yönetimi
- Dashboard ve istatistikler
- E-posta bildirimleri

## Teknolojiler

- **Backend:** Django 5.0
- **Frontend:**
  - TailwindCSS ve DaisyUI
  - Alpine.js (reaktif frontend)
  - HTMX (dinamik sayfa güncellemeleri)
- **Veritabanı:** SQLite (geliştirme), PostgreSQL (üretim)
- **Önbellek:** Redis
- **Görev Yöneticisi:** Celery

## Kurulum

### Gereksinimler

- Python 3.12+
- Node.js 18+
- PostgreSQL (üretim ortamı için)
- Redis (üretim ortamı için)

### Geliştirme Ortamı Kurulumu

1. Repoyu klonlayın ve proje dizinine gidin:

```bash
git clone https://github.com/vivacrm/vivacrm-v2.git
cd vivacrm-v2
```

2. Python sanal ortamı oluşturun ve aktifleştirin:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# veya
venv\Scripts\activate  # Windows
```

3. Python bağımlılıklarını yükleyin:

```bash
pip install -r requirements.txt
```

4. Frontend bağımlılıklarını yükleyin:

```bash
npm install
```

5. TailwindCSS'i derleyin:

```bash
npm run build
```

6. Veritabanını oluşturun:

```bash
python manage.py migrate
```

7. Örnek verileri yükleyin:

```bash
python manage.py loaddata fixtures/example_data.json
```

8. Geliştirme sunucusunu başlatın:

```bash
python manage.py runserver
```

9. TailwindCSS'i geliştirme modunda çalıştırın:

```bash
npm run dev
```

### Giriş Bilgileri

Örnek verileri yükledikten sonra, aşağıdaki bilgilerle giriş yapabilirsiniz:

- Admin Kullanıcı: `admin@example.com` / `adminpass`
- Normal Kullanıcı: `user@example.com` / `userpass`

## Kullanım Kılavuzu

Temel özellikler ve kullanım:

1. **Gösterge Paneli (Dashboard):** Sistem genel durum ve istatistikleri
2. **Müşteriler:** Müşteri ekleme, düzenleme, silme ve arama
3. **Ürünler:** Ürün ve stok yönetimi
4. **Siparişler:** Sipariş oluşturma ve yönetimi
5. **Faturalar:** Fatura oluşturma ve takibi
6. **Raporlar:** Satış, müşteri ve stok raporları
7. **Yönetim Paneli:** Sistem ayarları ve yönetimi

## Geliştirme

Projeye katkıda bulunmak için:

1. FRONTEND.md dosyasındaki frontend geliştirme talimatlarını okuyun
2. CLAUDE.md dosyasında belirtilen geliştirme planını takip edin
3. DESIGN_GUIDE.md dosyasındaki tasarım rehberini kullanarak tutarlı bir UI oluşturun
4. SECURITY.md dosyasındaki güvenlik uygulamalarını dikkate alın
5. MONITORING.md belgelerini izleyerek sistem izleme yapılandırmasını anlayın
6. USER_GUIDE.md dosyasını inceleyerek sistemin tüm özelliklerini tanıyın

## Dökümantasyon

Proje, aşağıdaki kapsamlı dokümantasyona sahiptir:

- **USER_GUIDE.md**: Kullanıcı kılavuzu ve özellik açıklamaları
- **DESIGN_GUIDE.md**: Tasarım prensipleri ve UI bileşenleri
- **SECURITY.md**: Güvenlik özellikleri ve en iyi uygulamalar
- **MONITORING.md**: İzleme ve loglama rehberi
- **CI-CD.md**: CI/CD pipeline ve deployment açıklamaları
- **FRONTEND.md**: Frontend teknolojileri ve geliştirme rehberi
- **README-Docker.md**: Docker kurulum ve yapılandırma talimatları

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.