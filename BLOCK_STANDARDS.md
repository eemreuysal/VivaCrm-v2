# VivaCRM v2 Django Şablon Blok Standartları

Bu döküman, VivaCRM v2 projesinde kullanılan Django şablon bloklarının standart isimlendirme ve kullanım kurallarını tanımlamaktadır. Tutarlı bir şablon yapısı için tüm geliştiricilerin bu standartlara uyması gerekmektedir.

## Temel Bloklar

Tüm şablonlarda kullanılabilecek temel bloklar:

| Blok Adı           | Kullanım Amacı                                | Varsayılan İçerik         |
|--------------------|--------------------------------------------|--------------------------|
| `title`            | Sayfa başlığı                              | "VivaCRM"                |
| `meta_tags`        | Ek meta etiketleri                         | Boş                      |
| `extra_css`        | Sayfa-spesifik CSS                         | Boş                      |
| `body_classes`     | Body etiketine ek sınıflar                 | Temel tema sınıfları     |
| `body_attrs`       | Body etiketine ek öznitelikler             | Boş                      |
| `content`          | Ana sayfa içeriği                          | Boş                      |
| `navbar`           | Üst navigasyon barı                        | Varsayılan navbar        |
| `sidebar`          | Kenar çubuğu menüsü                        | Varsayılan sidebar       |
| `footer`           | Sayfa alt bilgisi                          | Varsayılan footer        |
| `extra_js`         | Sayfa-spesifik JavaScript                  | Boş                      |

## İçerik Alt Blokları

`content` bloğu içinde kullanılabilecek standart alt bloklar:

| Blok Adı               | Kullanım Amacı                                |
|------------------------|-------------------------------------------|
| `page_header`          | Sayfa başlığı ve üst bilgiler              |
| `page_content`         | Ana sayfa içeriği                          |
| `page_sidebar`         | Sayfa-spesifik yan panel                   |
| `page_footer`          | Sayfa-spesifik alt bilgi                   |

## Form Blokları

Form içeren sayfalarda kullanılabilecek bloklar:

| Blok Adı               | Kullanım Amacı                                |
|------------------------|-------------------------------------------|
| `form_header`          | Form başlığı ve açıklaması                 |
| `form_fields`          | Form alanları                              |
| `form_actions`         | Form düğmeleri (submit, cancel, vb.)       |
| `form_footer`          | Form alt bilgileri                         |

## Dashboard Blokları

Dashboard sayfaları için özel bloklar:

| Blok Adı               | Kullanım Amacı                                |
|------------------------|-------------------------------------------|
| `dashboard_summary`    | Özet istatistikler                         |
| `dashboard_charts`     | Grafikler                                  |
| `dashboard_tables`     | Veri tabloları                             |
| `dashboard_sidebar`    | Dashboard yan panel                        |

## Modal Blokları

Modal diyaloglar için standart bloklar:

| Blok Adı               | Kullanım Amacı                                |
|------------------------|-------------------------------------------|
| `modal_header`         | Modal başlığı                              |
| `modal_body`           | Modal içeriği                              |
| `modal_footer`         | Modal alt bilgisi (düğmeler, vb.)          |

## Kullanım Kuralları

1. **Blok İsimleri**: Tüm blok isimleri küçük harfle ve altçizgi (_) ile ayrılarak yazılmalıdır.
2. **Yerleşim**: Bloklar, ana şablonda tanımlanan sırayla kullanılmalıdır.
3. **Boş Bloklar**: Bir blok kullanılmayacaksa, açıkça boşaltılmalıdır (`{% block blok_adı %}{% endblock %}`).
4. **İç İçe Bloklar**: Bir blok içinde başka bir blok tanımlanırken, üst blok içeriğini korumak için `{{ block.super }}` kullanılmalıdır.

## Örnekler

### Temel Sayfa Örneği

```html
{% extends "base.html" %}

{% block title %}Müşteri Listesi{% endblock %}

{% block content %}
  <div class="container mx-auto p-4">
    {% block page_header %}
      <h1 class="text-2xl font-bold mb-4">Müşteriler</h1>
    {% endblock %}
    
    {% block page_content %}
      <div class="bg-white rounded shadow p-4">
        <!-- Müşteri listesi içeriği -->
      </div>
    {% endblock %}
  </div>
{% endblock %}
```

### Form Örneği

```html
{% extends "base.html" %}

{% block title %}Yeni Müşteri{% endblock %}

{% block content %}
  <div class="container mx-auto p-4">
    {% block page_header %}
      <h1 class="text-2xl font-bold mb-4">Yeni Müşteri Ekle</h1>
    {% endblock %}
    
    <form method="post" class="bg-white rounded shadow p-4">
      {% csrf_token %}
      
      {% block form_header %}
        <p class="text-gray-600 mb-4">Lütfen müşteri bilgilerini giriniz.</p>
      {% endblock %}
      
      {% block form_fields %}
        {{ form.as_p }}
      {% endblock %}
      
      {% block form_actions %}
        <div class="flex justify-end mt-4">
          <button type="button" class="btn btn-outline mr-2">İptal</button>
          <button type="submit" class="btn btn-primary">Kaydet</button>
        </div>
      {% endblock %}
    </form>
  </div>
{% endblock %}
```

## Şablon Kalıtım Yapısı

```
base.html                              # Tüm sayfalar için temel şablon
├── base_auth.html                     # Kimlik doğrulama sayfaları için şablon
│   ├── login.html                     # Giriş sayfası
│   ├── register.html                  # Kayıt sayfası
│   └── password_reset.html            # Şifre sıfırlama sayfası
│
├── customers/
│   ├── customer_list.html             # Müşteri listesi sayfası
│   ├── customer_detail.html           # Müşteri detay sayfası
│   └── customer_form.html             # Müşteri form sayfası
│
├── products/
│   ├── product_list.html              # Ürün listesi sayfası
│   ├── product_detail.html            # Ürün detay sayfası
│   └── product_form.html              # Ürün form sayfası
│
└── dashboard/
    ├── dashboard.html                 # Ana kontrol paneli
    ├── sales_dashboard.html           # Satış kontrol paneli
    └── inventory_dashboard.html       # Envanter kontrol paneli
```

## Uyumluluk Kontrol Listesi

Yeni bir şablon oluştururken veya mevcut bir şablonu düzenlerken aşağıdaki kontrol listesini kullanın:

- [ ] Doğru şablondan kalıtım alınmış mı?
- [ ] Tüm gerekli bloklar tanımlanmış mı?
- [ ] Blok isimleri standartlara uygun mu?
- [ ] İç içe bloklar doğru kullanılmış mı?
- [ ] Sayfa başlığı belirtilmiş mi? (`title` bloğu)
- [ ] Sayfa-spesifik CSS ve JavaScript doğru bloklarda tanımlanmış mı?
- [ ] Mobil uyumluluk için gerekli sınıflar eklenmiş mi?

Bu standartlar, proje genelinde tutarlı ve bakımı kolay bir şablon yapısı sağlayacaktır.