# VivaCRM Şablon Block Standartları

Bu belge, VivaCRM v2 projesinde şablonlarda kullanılacak standart block yapısını tanımlar. 
Tüm şablonlar bu standartlara uygun olarak geliştirilmelidir.

## Standart Block Yapısı

```
- head_meta - Head bölümüne eklenen meta etiketleri
- title - Sayfa başlığı (<title> etiketi içeriği)
- head_extra - Head bölümüne eklenecek diğer içerikler
- extra_css - Ekstra CSS
- body_attributes - Body etiketine ek öznitelikler
- navbar - Üst navigasyon menüsü
- page_header - Sayfa başlığı ve açıklaması içeren üst bölüm
- body - Ana içerik kapsayıcısı
  - content - Sayfa içeriği
- sidebar - Yan menü (dashboard gibi sayfalarda)
- footer - Alt bilgi
- modals - Sayfa için tanımlanan modaller
- optional_js - İsteğe bağlı JavaScript (özellik/sayfa bazlı)
- extra_js - Ekstra JavaScript (sayfa özel kodları)
```

## Block Kullanım Kuralları

1. Her şablon en azından `content` bloğunu içermelidir.
2. Bloklar içi boş bırakıldığında varsayılan içeriği göstermelidir.
3. Üst şablonu tamamen geçersiz kılmak için `{{ block.super }}` kullanılmamalıdır.
4. Üst şablonun içeriğine ekleme yapmak için `{{ block.super }}` kullanılabilir.

## Örnekler

### Basit İçerik Sayfası
```html
{% extends "base/base.html" %}

{% block title %}Hakkımızda{% endblock %}

{% block content %}
<div class="container mx-auto py-8">
  <h1 class="text-3xl font-bold mb-4">Hakkımızda</h1>
  <p>İçerik burada...</p>
</div>
{% endblock %}
```

### Dashboard İçerik Sayfası
```html
{% extends "base/base_dashboard.html" %}

{% block title %}Ürünler{% endblock %}

{% block page_header %}
<div class="flex justify-between items-center mb-6">
  <h1 class="text-2xl font-bold">Ürünler</h1>
  <a href="{% url 'products:product-create' %}" class="btn btn-primary">Yeni Ürün</a>
</div>
{% endblock %}

{% block content %}
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <!-- İçerik burada... -->
  </div>
</div>
{% endblock %}
```