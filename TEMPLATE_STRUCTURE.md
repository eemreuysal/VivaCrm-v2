# VivaCRM v2 Şablon Yapısı Dökümantasyonu

Bu döküman, VivaCRM v2 projesinde yapılan şablon yapısı iyileştirmelerini ve mevcut şablon sisteminin nasıl kullanılacağını açıklamaktadır.

## Şablon Hiyerarşisi

```
base.html                       # Ana şablon, tüm sayfalar için temel yapı
├── base_auth.html              # Kimlik doğrulama sayfaları için temel şablon
│   ├── login.html              # Giriş sayfası
│   ├── register.html           # Kayıt sayfası
│   └── password_reset.html     # Şifre sıfırlama sayfası
└── base_design_system.html     # Tasarım sistemi için temel şablon
    └── design_system.html      # Tasarım sistemi dokümantasyon sayfası
```

## Parçalı Şablonlar (Partials)

Tekrar kullanılabilir şablon parçaları `templates/partials/` dizininde bulunmaktadır:

- `head.html` - HTML head bölümü
- `footer.html` - Sayfa alt bilgisi
- `navbar.html` - Üst navigasyon barı
- `sidebar.html` - Kenar çubuğu menüsü
- `toast_messages.html` - Bildirim mesajları
- `theme_switcher.html` - Tema değiştirici

## Include Dosyaları

Harici CSS ve JavaScript dosyalarını yöneten include dosyaları:

- `css_includes.html` - CSS dosyalarını yönetir, kritik CSS desteği içerir
- `js_includes.html` - JavaScript dosyalarını yönetir, koşullu yükleme destekler

## Block Yapısı

Tüm şablonlarda standart bir block yapısı kullanılmaktadır:

| Block Adı             | Amacı                                         | Konumu           |
|-----------------------|-----------------------------------------------|------------------|
| `title`               | Sayfa başlığı                                 | `<title>` etiketi içinde |
| `meta_tags`           | Ek meta etiketleri                            | `<head>` içinde  |
| `extra_css`           | Sayfa-spesifik CSS                            | `<head>` içinde  |
| `body_classes`        | Body etiketine ek sınıflar                    | `<body>` sınıf atributu |
| `body_attrs`          | Body etiketine ek atributlar                  | `<body>` etiketi |
| `content`             | Ana sayfa içeriği                             | `<main>` içinde  |
| `navbar`              | Üst navigasyon barı                           | `<header>` içinde |
| `sidebar`             | Kenar çubuğu menüsü                           | Ana içerik öncesi |
| `footer`              | Sayfa alt bilgisi                             | Ana içerik sonrası |
| `extra_js`            | Sayfa-spesifik JavaScript                     | `</body>` öncesi |

## CSS Include Kullanımı

`css_includes.html` dosyası şu parametreleri destekler:

```html
{% include "partials/css_includes.html" with use_critical_css=True %}
```

| Parametre           | Varsayılan | Açıklama                                      |
|---------------------|------------|----------------------------------------------|
| `use_critical_css`  | `False`    | Kritik CSS'i inline olarak ekler             |

## JavaScript Include Kullanımı

`js_includes.html` dosyası aşağıdaki parametreleri destekler:

```html
{% include "partials/js_includes.html" with need_charts=True need_alpine=True %}
```

| Parametre      | Varsayılan | Açıklama                                      |
|----------------|------------|----------------------------------------------|
| `need_alpine`  | `False`    | Alpine.js kütüphanesini yükler               |
| `need_charts`  | `False`    | ApexCharts kütüphanesini yükler              |
| `need_htmx`    | `False`    | HTMX kütüphanesini yükler                    |
| `need_datatable` | `False`  | DataTables kütüphanesini yükler              |

## Tema Yönetimi

Tema değiştirme mantığı `theme.js` dosyasında merkezi olarak yönetilmektedir. İki ana tema vardır:

- `vivacrm` - Açık tema
- `vivacrmDark` - Koyu tema

Tema değiştirici şu şekilde eklenebilir:

```html
{% include "partials/theme_switcher.html" %}
```

## Kullanım Örnekleri

### Basit Sayfa Oluşturma

```html
{% extends "base.html" %}

{% block title %}Sayfa Başlığı{% endblock %}

{% block content %}
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Sayfam</h1>
    <p>İçerik buraya...</p>
  </div>
{% endblock %}
```

### Özel CSS ve JavaScript İçeren Sayfa

```html
{% extends "base.html" %}

{% block title %}Özel Sayfa{% endblock %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/my-page.css' %}">
{% endblock %}

{% block content %}
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Özel Sayfam</h1>
    <div id="my-widget"></div>
  </div>
{% endblock %}

{% block extra_js %}
  <script src="{% static 'js/my-page.js' %}"></script>
{% endblock %}
```

### Grafik Kütüphanesi Kullanımı

```html
{% extends "base.html" %}
{% include "partials/js_includes.html" with need_charts=True %}

{% block title %}Grafik Sayfası{% endblock %}

{% block content %}
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Grafik Örneği</h1>
    <div id="myChart" class="w-full h-64"></div>
  </div>
{% endblock %}

{% block extra_js %}
  <script>
    // ApexCharts grafik kodu
    document.addEventListener('DOMContentLoaded', function() {
      var options = {
        chart: { type: 'line' },
        series: [{ name: 'Satışlar', data: [30, 40, 45, 50, 49, 60, 70, 91] }],
        xaxis: { categories: [1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998] }
      };
      
      var chart = new ApexCharts(document.querySelector("#myChart"), options);
      chart.render();
    });
  </script>
{% endblock %}
```

## En İyi Pratikler

1. **Tutarlı Block Yapısı Kullanın**: Block isimlerini standart isimlendirme şemasına göre kullanın.
2. **Modüler Düşünün**: Tekrar kullanılabilir bileşenler için partial şablonlar oluşturun.
3. **Gerekmeyen JS Kütüphanelerini Yüklemeyin**: Sadece ihtiyaç duyulan JavaScript kütüphanelerini koşullu olarak yükleyin.
4. **Kritik CSS Kullanın**: Hızlı sayfa yüklemesi için kritik CSS'i inline olarak ekleyin.
5. **Tema Değiştiriciyi Tutarlı Konumlandırın**: Tema değiştirici bileşenini kullanıcının kolayca erişebileceği tutarlı bir yere yerleştirin.

## Sorun Giderme

### Sık Karşılaşılan Sorunlar

1. **JavaScript Kütüphanesi Yüklenmiyor**: `js_includes.html` içindeki parametreler doğru kullanıldığından emin olun.
2. **Tema Değiştirme Çalışmıyor**: LocalStorage erişimi olup olmadığını kontrol edin.
3. **Block İçerikleri Görünmüyor**: Block isimlerinin doğru yazıldığından emin olun.

### Yeni Bir Kütüphane Ekleme

Yeni bir JavaScript kütüphanesini şablon sistemine eklemek için:

1. `js_includes.html` dosyasını düzenleyin
2. Yeni bir koşullu parametre ekleyin (örn. `need_datepicker`)
3. İlgili script etiketlerini koşula bağlı olarak ekleyin