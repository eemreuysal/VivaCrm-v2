# CSS ve JavaScript Dahil Etme Standardı

Bu doküman, VivaCRM v2 projesinde CSS ve JavaScript kaynaklarının nasıl dahil edilmesi gerektiğini açıklar. Proje, hem geleneksel statik dosya dahil etme yöntemini hem de modern Vite tabanlı bundling yaklaşımını destekler.

## İçerik Tablosu

1. [Genel Bakış](#genel-bakış)
2. [Unified Include Dosyaları](#unified-include-dosyaları)
3. [Kullanım Örnekleri](#kullanım-örnekleri)
4. [Vite Entegrasyonu](#vite-entegrasyonu)
5. [Performans Optimizasyonları](#performans-optimizasyonları)

## Genel Bakış

Projemiz, aşağıdaki yaklaşımları destekler:

1. **Geleneksel Statik Dosya Dahil Etme**: 
   - CSS ve JS dosyaları doğrudan `<link>` ve `<script>` etiketleri ile dahil edilir
   - Geliştirme/prodüksiyon ortamları için farklı dosyalar kullanılır (minified vs non-minified)

2. **Vite Tabanlı Bundling**:
   - JS entry point üzerinden CSS dahil edilir (CSS modülleri JS'de import edilir)
   - Modern JavaScript modül sistemi kullanılır
   - HMR (Hot Module Replacement) geliştirme sırasında desteklenir

## Unified Include Dosyaları

Tutarlılık için aşağıdaki merkezi include dosyalarını kullanın:

### 1. `includes/css_unified.html`

```django
{% include 'includes/css_unified.html' with 
   use_vite=True|False           # Vite entegrasyonu kullanılsın mı? (varsayılan: settings.USE_VITE)
   use_critical_css=True|False   # Kritik CSS kullanılsın mı? (varsayılan: False)
   preload_fonts=True|False      # Font preloading yapılsın mı? (varsayılan: True)
%}
```

### 2. `includes/js_unified.html`

```django
{% include 'includes/js_unified.html' with 
   use_vite=True|False           # Vite entegrasyonu kullanılsın mı? (varsayılan: settings.USE_VITE)
   defer=True|False              # JS'lerin defer özniteliği (varsayılan: True)
   need_charts=True|False        # Grafik kütüphanesi ihtiyacı (varsayılan: False)
   need_htmx=True|False          # HTMX ihtiyacı (varsayılan: True)
   need_alpine=True|False        # Alpine.js ihtiyacı (varsayılan: True)
   environment="production"      # Environment adı (varsayılan: "production")
%}
```

### 3. `includes/head_unified.html`

```django
{% include 'includes/head_unified.html' with 
   title="Sayfa Başlığı"           # Sayfa başlığı (opsiyonel)
   description="Sayfa açıklaması"  # Sayfa açıklaması (opsiyonel)
   use_vite=True|False             # Vite entegrasyonu kullanılsın mı? (varsayılan: settings.USE_VITE)
   use_critical_css=True|False     # Kritik CSS kullanılsın mı? (varsayılan: False)
%}
```

## Kullanım Örnekleri

### Temel Şablon (base_unified.html)

`base_unified.html` şablonu, yeni standardın nasıl kullanılacağını gösteren bir örnektir:

```django
<!DOCTYPE html>
<html lang="tr" data-theme="vivacrm">
<head>
    {% include 'includes/head_unified.html' with 
        title=title|default:None 
        use_vite=use_vite|default:settings.USE_VITE 
    %}
</head>
<body>
    {% block content %}{% endblock %}
    
    {% include 'includes/js_unified.html' with 
        use_vite=use_vite|default:settings.USE_VITE 
        need_charts=need_charts|default:False 
    %}
</body>
</html>
```

### Performans Odaklı Sayfa

Kritik CSS ve font preloading ile optimize edilmiş bir sayfa örneği:

```django
<!DOCTYPE html>
<html lang="tr" data-theme="vivacrm" class="no-js">
<head>
    {% include 'includes/head_unified.html' with 
        use_critical_css=True 
        use_vite=False 
    %}
    
    <!-- Inline Critical CSS -->
    <style>
        /* Critical CSS buraya */
    </style>
    
    <script>
        // Remove no-js class
        document.documentElement.classList.remove('no-js');
    </script>
</head>
<body>
    <!-- Content -->
    
    {% include 'includes/js_unified.html' with defer=True %}
</body>
</html>
```

## Vite Entegrasyonu

Vite entegrasyonu için gerekli konfigürasyon:

1. Django settings içinde:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_vite",
]

USE_VITE = True  # Global Vite kullanım bayrağı
VITE_APP_DIR = BASE_DIR
VITE_DEV_MODE = DEBUG
VITE_DEV_SERVER_URL = "http://localhost:3000"
```

2. package.json içinde:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "alpinejs": "^3.13.5",
    "htmx.org": "^1.9.10"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

3. JS içinden CSS import etme:

```javascript
// main.js
import '../css/src/main.css';

// Kod buraya...
```

## Performans Optimizasyonları

Şablonlarımızda kullanılan performans optimizasyonları:

1. **Font Preloading**: Kritik fontlar `preload` ile yüklenir
2. **CSS Defer Loading**: Kritik olmayan CSS'ler defer yöntemiyle yüklenir
3. **Critical CSS**: Sayfanın üst kısmı için gerekli kritik CSS'ler inline olarak eklenir
4. **JS Loading**: 
   - `defer` özniteliği ile JS'ler sayfayı bloke etmez
   - Yalnızca gerekli kütüphaneler dahil edilir (`need_charts` vb. parametrelerle)
5. **Alpine.js Optimizasyonu**: Alpine.js temel modülü senkron, ek modüller deferlanır