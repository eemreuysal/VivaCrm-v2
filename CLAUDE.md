# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# VivaCRM v2 - Kod Yapısı ve Tasarım Standartları Dokümantasyonu

## 0. Geliştirme Komutları

### Django Geliştirme Sunucusu

```bash
# Standart Django geliştirme sunucusu
python manage.py runserver

# veya özel betik (tüm bağımlılıkları kontrol eder ve CSS build işlemini yapar)
./scripts/start_dev.sh
```

### Veritabanı İşlemleri

```bash
# Migrasyonları uygula
python manage.py migrate

# Yeni migrasyon oluştur
python manage.py makemigrations

# Migrasyon durumunu göster
python manage.py showmigrations
```

### Frontend Asset'leri

```bash
# CSS yapılandırma
npm run build:css           # CSS dosyalarını derle
npm run watch:css           # CSS değişikliklerini izle
npm run build:css:prod      # Üretim için CSS dosyalarını derle

# Tüm asset'leri yapılandır (Vite)
npm run build               # Tüm asset'leri yapılandır
npm run dev                 # Vite geliştirme sunucusunu başlat

# Statik dosyaları topla
python manage.py collectstatic --noinput
```

### Linting ve Format

```bash
# JavaScript ve CSS dosyalarını formatla
npm run format

# JavaScript lint
npm run lint                # JavaScript dosyalarını lint et
npm run lint:fix            # JavaScript lint sorunlarını düzelt

# CSS lint
npm run lint:css            # CSS dosyalarını lint et
npm run lint:css:fix        # CSS lint sorunlarını düzelt

# TypeScript kontrol
npm run type-check          # TypeScript kontrolü yap
```

### Test

```bash
# Tüm testleri çalıştır
python manage.py test

# Belirli bir uygulama için testleri çalıştır
python manage.py test [uygulama_adı]
# Örnek: python manage.py test dashboard
```

### Docker ile Geliştirme

```bash
# Geliştirme stack'ini çalıştır
docker-compose -f docker-compose.dev.yml up

# Üretim stack'ini çalıştır 
docker-compose up

# İzleme stack'ini çalıştır
docker-compose -f docker-compose.monitoring.yml up
```

### Güvenlik Taraması

```bash
# Güvenlik taraması çalıştır
./scripts/security_scan.sh
```

### Önbellek Yönetimi

```bash
# Önbellek istatistiklerini kontrol et
python manage.py cache_stats

# Önbelleği ısıt
python manage.py cache_warm
```

### Veritabanı Optimizasyonu

```bash
# Veritabanı optimizasyonu yap
python manage.py optimize_db
```

## 1. Proje Genel Yapısı

### 1.1. Klasör Organizasyonu

```
VivaCRM v2/
├── accounts/           # Kullanıcı yönetimi ve kimlik doğrulama
├── admin_panel/        # Admin panel işlevleri
├── core/               # Sistem çekirdek işlevleri
├── customers/          # Müşteri yönetimi
├── dashboard/          # Dashboard modülü
├── invoices/           # Fatura işlemleri
├── orders/             # Sipariş yönetimi
├── products/           # Ürün yönetimi
├── reports/            # Raporlama modülü
├── static/             # Statik dosyalar (JS, CSS, görsel)
│   ├── css/            # CSS dosyaları
│   │   ├── src/        # Kaynak CSS dosyaları
│   │   └── dist/       # Derlenmiş CSS dosyaları
│   └── js/             # JavaScript dosyaları
│       ├── alpine/     # Alpine.js bileşenleri
│       ├── components/ # JS bileşenleri
│       ├── core/       # Çekirdek JS işlevleri
│       ├── htmx/       # HTMX yardımcıları
│       ├── modules/    # JS modülleri
│       └── store/      # Durum yönetimi
└── templates/          # HTML şablonları
    ├── accounts/       # Kullanıcı şablonları
    ├── base/           # Temel şablonlar (tüm sayfalarca kullanılan)
    ├── components/     # Yeniden kullanılabilir bileşenler
    ├── customers/      # Müşteri şablonları
    └── ...             # Diğer modül şablonları
```

### 1.2. Teknoloji Yığını

- **Backend**: Django 5.0 (Python)
- **Frontend**:
  - HTMX (Sayfa yenileme olmadan içerik güncellemesi)
  - Alpine.js (Reaktif UI bileşenleri)
  - TailwindCSS (Utility-first CSS framework)
  - DaisyUI (TailwindCSS bileşen kütüphanesi)
- **Veritabanı**: PostgreSQL
- **Önbellek**: Redis
- **Görev Yöneticisi**: Celery

## 2. Frontend Mimarisi

### 2.1. Template Sistemi Prensipleri

#### Template Hiyerarşisi

```
base/base.html                    # Ana temel şablon
├── base/base_auth.html           # Kimlik doğrulama sayfaları şablonu
└── base/base_dashboard.html      # Dashboard sayfaları şablonu
    ├── dashboard/dashboard.html  # Ana dashboard
    ├── customers/list.html       # Müşteri listesi
    ├── products/list.html        # Ürün listesi
    └── ...                       # Diğer sayfa şablonları
```

#### Template İçeriği Kuralları

1. **Head Bölümü**: Tüm meta etiketleri, CSS bağlantıları ve kritik JS `base.html` içinde tanımlanır.
2. **Body Yapısı**: Her sayfa en az aşağıdaki blokları içermelidir:
   - `{% block content %}` - Ana içerik için
   - `{% block page_title %}` - Sayfa başlığı için
   - `{% block extra_css %}` - Sayfaya özel CSS için
   - `{% block extra_js %}` - Sayfaya özel JS için

#### Bileşen Şablonları Kullanımı

```html
{% include "components/card.html" with title="Müşteri Özeti" content=customer_summary %}
```

### 2.2. CSS Mimarisi (TailwindCSS + DaisyUI)

#### CSS Dosya Yapısı

```
static/css/src/
├── 00-settings/      # Değişkenler, tema ayarları, DaisyUI yapılandırması
├── 02-generic/       # Genel stil tanımlamaları
├── 03-elements/      # Temel HTML öğeleri için stiller
├── 05-components/    # Bileşen stilleri
├── 06-themes/        # Tema tanımlamaları (açık/koyu)
└── 07-utilities/     # Yardımcı sınıflar
```

#### TailwindCSS Yapılandırma Kuralları

- Proje için özel renkler `tailwind.config.js` dosyasında tanımlanır:
  - Marka renkleri: `viva-primary`, `viva-secondary`, vb.
  - Tema renkleri: Açık ve koyu tema için uygun renkler

#### CSS Yazdırma Prensipleri

1. **Inline Tailwind Kullanımı**: Bileşene özel, tekrarlanmayan stiller için HTML içinde.
2. **Bileşen CSS**: Yeniden kullanılabilir, karmaşık bileşenler için `/static/css/src/05-components/` klasöründe.
3. **Genel Temalar**: Tema değişiklikleri için `/static/css/src/06-themes/` klasöründe.

### 2.3. JavaScript Mimarisi (Alpine.js + HTMX)

#### JavaScript Dosya Yapısı

```
static/js/
├── alpine/                 # Alpine.js bileşenleri ve yapılandırması
│   ├── components/         # UI bileşenleri (modal, card, vb.)
│   ├── helpers/            # Yardımcı fonksiyonlar (formatters, vb.)
│   └── stores/             # Merkezi durum yönetimi (theme, vb.)
├── core/                   # Çekirdek işlevler
├── htmx/                   # HTMX yardımcıları ve eventler
├── components/             # Sayfa özel bileşenleri
└── store/                  # Uygulama düzeyinde durum yönetimi
```

#### Alpine.js Kullanım Prensipleri

1. **Modüler Yapı**: Her Alpine.js bileşeni kendi dosyasında tanımlanır.
2. **Merkezi Durum Yönetimi**: Tema gibi global durumlar için Alpine store kullanılır.
3. **Bileşen Tanımı Örneği**:

```javascript
// static/js/alpine/components/modal.js
export default function modal() {
  return {
    open: false,
    title: '',
    init() {
      // Bileşen başlatma kodu
    },
    toggle() {
      this.open = !this.open;
    }
  }
}
```

#### HTMX Kullanım Prensipleri

1. **Bir Sayfada Kısmi Yenileme**: Sayfa yükleme olmadan içeriği güncellemek için kullanılır.
2. **Öznitelik Tabanlı**: HTML öğelerinde `hx-*` öznitelikleri kullanılır.
3. **Event Yönetimi**: Olaylar `/static/js/htmx/helpers.js` içinde tanımlanır.

```html
<!-- HTMX kullanım örneği -->
<button hx-get="/customers/list/" 
        hx-target="#customer-list" 
        hx-trigger="click">
  Müşterileri Yenile
</button>
```

## 3. Bileşen Sistemi

### 3.1. Temel Bileşenler

#### Card Bileşeni

```html
<!-- templates/components/card.html -->
<div class="card bg-base-100 shadow-xl" x-data="card()">
  {% if title %}
  <div class="card-header p-4 border-b">
    <h3 class="card-title text-lg font-medium">{{ title }}</h3>
    {% if collapsible %}
    <button @click="toggle()" class="btn btn-sm btn-ghost">
      <i :class="open ? 'fa-chevron-up' : 'fa-chevron-down'" class="fas"></i>
    </button>
    {% endif %}
  </div>
  {% endif %}
  
  <div class="card-body p-5" x-show="open">
    {{ content|safe }}
  </div>
</div>
```

#### Modal Bileşeni

```html
<!-- templates/components/modal.html -->
<div id="{{ id|default:'modal' }}" x-data="modal()" class="modal" :class="{ 'modal-open': open }">
  <div class="modal-box">
    <h3 class="font-bold text-lg">{{ title }}</h3>
    <div class="py-4">
      {{ content|safe }}
    </div>
    <div class="modal-action">
      {% if show_cancel %}
      <button @click="open = false" class="btn">İptal</button>
      {% endif %}
      <button @click="onConfirm()" class="btn btn-primary">{{ confirm_text|default:'Tamam' }}</button>
    </div>
  </div>
</div>
```

#### Responsive Table Bileşeni

```html
<!-- templates/components/responsive_table.html -->
<div x-data="{ 
  cardMode: false,
  screenWidth: window.innerWidth,
  checkMode() {
    this.cardMode = this.screenWidth < 768;
  }
}" x-init="checkMode(); window.addEventListener('resize', () => { screenWidth = window.innerWidth; checkMode(); })">

  <!-- Mobil görünüm: Kart yapısı -->
  <div x-show="cardMode" class="grid grid-cols-1 gap-4">
    {% for item in items %}
    <div class="card bg-base-100 shadow-sm">
      <!-- Kart içeriği -->
    </div>
    {% endfor %}
  </div>
  
  <!-- Masaüstü görünüm: Tablo yapısı -->
  <div x-show="!cardMode" class="overflow-x-auto">
    <table class="table w-full">
      <thead>
        <tr>
          {% for header in headers %}
          <th>{{ header }}</th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        <!-- Tablo satırları -->
      </tbody>
    </table>
  </div>
</div>
```

### 3.2. Form Bileşenleri

#### Form Wrapper Bileşeni

```html
<!-- templates/components/form.html -->
<form id="{{ id|default:'form' }}"
      method="{{ method|default:'post' }}"
      action="{{ url }}"
      x-data="{ 
        isSubmitting: false,
        validationErrors: {},
        submitForm() {
          this.isSubmitting = true;
          // Form gönderme kodu
        }
      }"
      @submit="submitForm()">
  {% csrf_token %}
  <div class="space-y-4">
    {{ content|safe }}
  </div>
  
  <div class="mt-6">
    <button type="submit" 
            class="btn btn-primary w-full sm:w-auto" 
            :disabled="isSubmitting">
      <span x-show="isSubmitting" class="loading loading-spinner"></span>
      {{ submit_text|default:'Kaydet' }}
    </button>
  </div>
</form>
```

#### Input Bileşeni

```html
<!-- templates/components/input.html -->
<div class="form-control">
  <label class="label" for="{{ id }}">
    <span class="label-text">{{ label }}{% if required %} *{% endif %}</span>
  </label>
  <input type="{{ type|default:'text' }}"
         id="{{ id }}"
         name="{{ name }}"
         placeholder="{{ placeholder|default:'' }}"
         value="{{ value|default:'' }}"
         class="input input-bordered w-full"
         {% if required %}required{% endif %}
         {% if disabled %}disabled{% endif %}>
  
  <label class="label" x-show="validationErrors.{{ name }}">
    <span class="label-text-alt text-error" x-text="validationErrors.{{ name }}"></span>
  </label>
</div>
```

## 4. Tema Bütünlüğü

### 4.1. Renk Şeması

#### Ana Renk Sistemi

- **Marka Renkleri**
  - `viva-primary`: Yeşil tonları (#22c55e, vb.)
  - `viva-secondary`: Mavi tonları (#0ea5e9, vb.)
  - `viva-accent`: Vurgu rengi (#f59e0b, vb.)

- **Gri Tonları**
  - `viva-gray-50` - `viva-gray-900`: Gri tonları

- **Özel Durumlar**
  - `viva-success`: Başarı durumu (#10b981)
  - `viva-warning`: Uyarı durumu (#f59e0b)
  - `viva-error`: Hata durumu (#ef4444)
  - `viva-info`: Bilgi durumu (#3b82f6)

#### Tema Renkleri (DaisyUI)

```javascript
// tailwind.config.js
module.exports = {
  // ...
  daisyui: {
    themes: [
      {
        light: {
          "primary": "#22c55e",
          "secondary": "#0ea5e9",
          "accent": "#f59e0b",
          "neutral": "#374151",
          "base-100": "#ffffff",
          "base-200": "#f3f4f6",
          "base-300": "#e5e7eb",
          "info": "#3b82f6",
          "success": "#10b981",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
        dark: {
          "primary": "#4ade80",
          "secondary": "#38bdf8",
          "accent": "#fbbf24",
          "neutral": "#d1d5db",
          "base-100": "#1f2937",
          "base-200": "#111827",
          "base-300": "#0f172a",
          "info": "#60a5fa",
          "success": "#34d399",
          "warning": "#fbbf24",
          "error": "#f87171",
        }
      }
    ]
  }
}
```

### 4.2. Tipografi

#### Font Ailesi

- **Ana Font**: 'Inter', sans-serif
- **Başlık Fontu**: 'Poppins', sans-serif
- **Monospace Font**: 'Fira Code', monospace (kod blokları için)

#### Font Boyutu Sistemi

- `text-xs`: 0.75rem (12px)
- `text-sm`: 0.875rem (14px)
- `text-base`: 1rem (16px)
- `text-lg`: 1.125rem (18px)
- `text-xl`: 1.25rem (20px)
- `text-2xl`: 1.5rem (24px)
- `text-3xl`: 1.875rem (30px)
- `text-4xl`: 2.25rem (36px)

#### Başlık Hiyerarşisi

- `h1`: 2.25rem, font-bold (Ana sayfa başlıkları)
- `h2`: 1.875rem, font-semibold (Bölüm başlıkları)
- `h3`: 1.5rem, font-medium (Alt bölüm başlıkları)
- `h4`: 1.25rem, font-medium (Kart başlıkları)
- `h5`: 1.125rem, font-medium (Vurgulu metinler)
- `h6`: 1rem, font-medium (Alt başlıklar)

### 4.3. Açık/Koyu Tema Yönetimi

Tema yönetimi alpine.js store ile merkezi olarak yönetilir:

```javascript
// static/js/alpine/stores/theme.js
export function useThemeStore() {
  return {
    darkMode: localStorage.getItem('vivacrm-theme') === 'dark',
    systemPreference: window.matchMedia('(prefers-color-scheme: dark)').matches,
    
    init() {
      if (localStorage.getItem('vivacrm-theme') === null) {
        this.useSystemPreference();
      } else {
        this.applyTheme(this.darkMode ? 'dark' : 'light');
      }
      
      // Sistem tercihi değişimini izle
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (localStorage.getItem('vivacrm-theme-source') === 'system') {
          this.darkMode = e.matches;
          this.applyTheme(this.darkMode ? 'dark' : 'light');
        }
      });
    },
    
    toggle() {
      this.darkMode = !this.darkMode;
      localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
      localStorage.setItem('vivacrm-theme-source', 'manual');
      this.applyTheme(this.darkMode ? 'dark' : 'light');
    },
    
    useSystemPreference() {
      this.darkMode = this.systemPreference;
      localStorage.setItem('vivacrm-theme-source', 'system');
      localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
      this.applyTheme(this.darkMode ? 'dark' : 'light');
    },
    
    applyTheme(theme) {
      if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.classList.remove('dark');
      }
    }
  }
}
```

Kullanımı:

```html
<div x-data x-init="$store.theme.init()">
  <button @click="$store.theme.toggle()">
    <i class="fas" :class="$store.theme.darkMode ? 'fa-sun' : 'fa-moon'"></i>
    <span x-text="$store.theme.darkMode ? 'Açık Tema' : 'Koyu Tema'"></span>
  </button>
</div>
```

## 5. Geliştirme Standartları

### 5.1. Kod Yazım Kuralları

#### Python (Backend)

- **Stil**: PEP 8 kurallarına uygun
- **Docstrings**: Google stilinde docstrings (özet, açıklama, args, returns)
- **İsimlendirme**: 
  - Sınıflar: PascalCase (ör. `CustomerService`)
  - Metodlar/Fonksiyonlar: snake_case (ör. `get_active_customers`)
  - Modüller: snake_case (ör. `order_utils.py`)

#### HTML (Templates)

- **Girintileme**: 2 boşluk
- **Blok Düzeni**: Django template blokları arasında 1 boş satır
- **Bileşen İsimleri**: snake_case (ör. `responsive_table.html`)
- **Blok İsimleri**: snake_case (ör. `{% block page_content %}`)

#### JavaScript

- **Stil**: ESLint kurallarına uygun
- **İsimlendirme**: 
  - Fonksiyonlar: camelCase (ör. `formatCurrency()`)
  - Bileşenler: PascalCase (ör. `UserProfile`)
  - Dosyalar: kebab-case (ör. `theme-manager.js`)
- **Modüler Yapı**: ES6 import/export kullanımı

#### CSS

- **Sınıf İsimlendirme**: kebab-case (ör. `card-header`)
- **TailwindCSS Direktifleri**: Grup direktiflerini kullan (`@layer components { ... }`)
- **CSS Değişkenleri**: Özellikler için CSS değişkenleri kullan (ör. `--viva-border-radius`)

### 5.2. Git İş Akışı

#### Branch Stratejisi

- **Main**: Kararlı, production-ready kod
- **Development**: Geliştirme branch'i
- **Feature Branches**: `feature/[özellik-adı]` formatında
- **Bugfix Branches**: `bugfix/[hata-adı]` formatında
- **Release Branches**: `release/v[sürüm]` formatında

#### Commit Mesajları

- **Format**: `[type]: [kısa açıklama]` (ör. `feat: Müşteri arama özelliği eklendi`)
- **Tipler**: 
  - `feat`: Yeni özellik
  - `fix`: Hata düzeltmesi
  - `refactor`: Kod iyileştirmesi
  - `docs`: Doküman değişiklikleri
  - `style`: Stil değişiklikleri (formatlama vb.)
  - `perf`: Performans iyileştirmeleri

#### Pull Request Süreci

1. Feature branch oluştur ve geliştirmeyi orada yap
2. Development branch'ine PR oluştur
3. PR'ı gözden geçir (kod kalitesi, test, doküman)
4. PR'ı birleştir, feature branch'i sil

### 5.3. Test Stratejisi

#### Test Seviyeleri

- **Unit Tests**: Bağımsız fonksiyonlar ve sınıflar için
- **Integration Tests**: Modül entegrasyonları için
- **End-to-End Tests**: Kullanıcı senaryoları için

#### Test İsimlendirme Kuralı

```python
def test_should_return_active_customers_when_filter_is_active():
    # Test kodu
```

## 6. Dokümantasyon Standartları

### 6.1. Kod Dokümantasyonu

#### Python Docstrings

```python
def get_customer_orders(customer_id, status=None, limit=10):
    """Bir müşterinin siparişlerini alır.
    
    Args:
        customer_id (int): Müşteri ID'si
        status (str, optional): Sipariş durumu filtresi
        limit (int, optional): Maksimum sipariş sayısı
        
    Returns:
        QuerySet: Sipariş nesneleri
        
    Raises:
        ValueError: Geçersiz sipariş durumu belirtildiğinde
    """
    # Fonksiyon içeriği
```

#### JavaScript JSDoc

```javascript
/**
 * Bir sayıyı para birimi formatına dönüştürür
 * 
 * @param {number} amount - Formatlanacak miktar
 * @param {string} [currency='TL'] - Para birimi
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @returns {string} Formatlanmış para birimi
 */
function formatCurrency(amount, currency = 'TL', locale = 'tr-TR') {
  // Fonksiyon içeriği
}
```

### 6.2. Bileşen Dokümantasyonu

Her bileşen için `/static/js/docs/` veya `/templates/components/README.md` içinde kullanım örnekleri ve parametreler belgelenmeli.

```markdown
# Card Bileşeni

Bilgileri gruplamak için kullanılır.

## Parametreler

| Parametre    | Tip      | Varsayılan | Açıklama                           |
|--------------|----------|------------|-----------------------------------|
| title        | string   | null       | Kart başlığı                       |
| content      | HTML     | null       | Kart içeriği                       |
| collapsible  | boolean  | false      | Kartın daraltılabilir olup olmadığı |

## Kullanım Örneği

```html
{% include "components/card.html" with 
   title="Müşteri Bilgileri" 
   content=customer_details 
   collapsible=True 
%}
```
```