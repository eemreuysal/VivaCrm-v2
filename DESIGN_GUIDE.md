# VivaCRM v2 Tasarım Rehberi

Bu rehber, VivaCRM v2 uygulamasına yeni sayfalar eklerken veya mevcut sayfaları düzenlerken izlemeniz gereken tasarım prensiplerini ve bileşenlerini içerir.

## İçindekiler

1. [Genel Tasarım Prensipleri](#genel-tasarım-prensipleri)
2. [Renk Paleti](#renk-paleti)
3. [Tipografi](#tipografi)
4. [Bileşenler](#bileşenler)
5. [Sayfa Yapısı](#sayfa-yapısı)
6. [Duyarlı Tasarım](#duyarlı-tasarım)
7. [Tema Desteği](#tema-desteği)
8. [HTMX ve Alpine.js Kullanımı](#htmx-ve-alpinejs-kullanımı)

## Genel Tasarım Prensipleri

VivaCRM v2, modern ve kullanıcı dostu bir arayüz sunar. Tasarım yaparken aşağıdaki prensipleri göz önünde bulundurun:

- **Tutarlılık**: Tüm sayfalarda aynı bileşenleri, renkleri ve stili kullanın
- **Basitlik**: Gereksiz öğelerden kaçının, kullanıcıların dikkatini dağıtmayın
- **Erişilebilirlik**: Tüm kullanıcılar için erişilebilir bir tasarım oluşturun
- **Duyarlılık**: Mobil, tablet ve masaüstü görünümlerini destekleyin
- **Performans**: Sayfa yükleme sürelerini optimize edin

## Renk Paleti

Uygulama, tailwind.config.js dosyasında tanımlanan özelleştirilmiş bir renk paleti kullanır. Ana renkler:

### Birincil Renkler (Primary)

- Ana mavi renk: `#3180ff` (primary-500)
- Açık ton: `#59acff` (primary-400)
- Koyu ton: `#1b4ae4` (primary-700)

### İkincil Renkler (Secondary)

- Ana gri renk: `#657799` (secondary-500)
- Açık ton: `#8494b2` (secondary-400)
- Koyu ton: `#424d67` (secondary-700)

### Durum Renkleri

- Başarı: `#1fcb76` (success-500)
- Uyarı: `#ffa50d` (warning-500)
- Hata: `#fa3642` (error-500)
- Bilgi: `#51a5ff` (info)

### Renkleri Kullanma

Renkleri kullanırken, DaisyUI'nin renk sınıflarını kullanın:

```html
<button class="btn btn-primary">Birincil Buton</button>
<div class="text-secondary-700">İkincil metin</div>
<div class="bg-success-100">Başarı arka planı</div>
```

## Tipografi

VivaCRM v2, Inter yazı tipini kullanır. Yazı boyutları ve ağırlıkları için Tailwind CSS sınıflarını kullanın:

### Başlıklar

- H1: `text-3xl font-bold`
- H2: `text-2xl font-bold`
- H3: `text-xl font-semibold`
- H4: `text-lg font-semibold`

### Metinler

- Normal metin: `text-base`
- Küçük metin: `text-sm`
- Çok küçük metin: `text-xs`

### Örnek

```html
<h1 class="text-3xl font-bold mb-4">Sayfa Başlığı</h1>
<h2 class="text-2xl font-bold mb-3">Bölüm Başlığı</h2>
<p class="text-base mb-2">Normal metin içeriği burada yer alır.</p>
<p class="text-sm text-secondary-500">Daha küçük açıklama metni.</p>
```

## Bileşenler

VivaCRM v2, hazır bileşenler kullanarak hızlı ve tutarlı sayfa tasarımları oluşturmanıza olanak tanır.

### Kartlar

Kartlar, içeriği gruplamak için kullanılan temel bileşenlerdir. `/templates/components/card.html` şablonunu kullanabilirsiniz:

```html
{% include "components/card.html" with title="Kart Başlığı" %}
  {% block content %}
    Kart içeriği buraya gelir
  {% endblock %}
  
  {% block actions %}
    <a href="#" class="btn btn-primary">İşlem Butonu</a>
  {% endblock %}
{% include "components/card.html" %}
```

Özelleştirme seçenekleri:
- `title`: Kart başlığı
- `subtitle`: Alt başlık (opsiyonel)
- `image`: Kart resmi URL'si (opsiyonel)
- `class`: Ek CSS sınıfları (opsiyonel)
- `collapsible`: Katlanabilir kart (opsiyonel, boolean)
- `collapsed`: Başlangıçta katlanmış durumda (opsiyonel, boolean)
- `border_color`: Kenarlık rengi (opsiyonel, örn: "primary", "success")

### Veri Tabloları

Veri tabloları, `/templates/components/data_table.html` şablonu ile oluşturulur:

```html
{% include "components/data_table.html" with 
  objects=customers 
  columns="name,email,phone,created_at" 
  headers="Ad,E-posta,Telefon,Kayıt Tarihi" 
  actions=True 
  title="Müşteriler" 
  add_url="customers:customer-create" 
  detail_url_name="customers:customer-detail" 
  edit_url_name="customers:customer-update" 
  delete_url_name="customers:customer-delete" 
%}
```

Özelleştirme seçenekleri:
- `objects`: Gösterilecek nesnelerin listesi
- `columns`: Gösterilecek sütunlar (virgülle ayrılmış)
- `headers`: Sütun başlıkları (virgülle ayrılmış)
- `actions`: İşlem butonlarını göster (opsiyonel, boolean)
- `title`: Tablo başlığı
- `add_url`: Yeni kayıt ekleme URL'si (opsiyonel)
- `detail_url_name`: Detay sayfası URL adı (opsiyonel)
- `edit_url_name`: Düzenleme sayfası URL adı (opsiyonel)
- `delete_url_name`: Silme işlemi URL adı (opsiyonel)

### Formlar

Form bileşenleri, `/templates/components/form.html` şablonu ile kullanılır:

```html
<form method="post" class="form-control w-full" enctype="multipart/form-data">
  {% csrf_token %}
  
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    {% for field in form %}
      <div class="form-control w-full">
        <label class="label">
          <span class="label-text">{{ field.label }}</span>
        </label>
        {{ field }}
        {% if field.errors %}
          <label class="label">
            <span class="label-text-alt text-error">{{ field.errors }}</span>
          </label>
        {% endif %}
      </div>
    {% endfor %}
  </div>
  
  <div class="mt-6 flex justify-end">
    <button type="submit" class="btn btn-primary">Kaydet</button>
  </div>
</form>
```

### İstatistik Kartları

İstatistik kartları için `/templates/components/stats_card.html` şablonunu kullanabilirsiniz:

```html
{% include "components/stats_card.html" with 
  title="Toplam Satış" 
  value="₺12,345" 
  change="15" 
  change_type="increase"
  icon="fa-solid fa-money-bill-wave" 
%}
```

## Sayfa Yapısı

Yeni bir sayfa oluştururken, mevcut yapıyı takip edin:

```html
{% extends "base/base.html" %}

{% block title %}Sayfa Başlığı - VivaCRM{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
  <div class="mb-6">
    <h1 class="text-3xl font-bold">Sayfa Başlığı</h1>
    <p class="text-secondary-500">Sayfa açıklaması burada yer alır.</p>
  </div>
  
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Sol sütun -->
    <div class="lg:col-span-2">
      <!-- Ana içerik -->
      {% include "components/card.html" with title="Ana İçerik" %}
        <!-- Kart içeriği -->
      {% include "components/card.html" %}
    </div>
    
    <!-- Sağ sütun -->
    <div>
      <!-- Yan panel -->
      {% include "components/card.html" with title="Yan Panel" %}
        <!-- Kart içeriği -->
      {% include "components/card.html" %}
    </div>
  </div>
</div>
{% endblock %}
```

## Duyarlı Tasarım

VivaCRM v2, Tailwind CSS'in duyarlı tasarım sınıflarını kullanır. Her zaman mobilden başlayarak tasarım yapın:

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- İçerik -->
</div>

<div class="hidden md:block">
  <!-- Sadece tablet ve masaüstünde görünen içerik -->
</div>

<div class="block md:hidden">
  <!-- Sadece mobilde görünen içerik -->
</div>
```

## Tema Desteği

VivaCRM v2, açık ve koyu tema arasında geçiş yapabilir. Temaya özgü bileşenler oluştururken, DaisyUI'nin tema değişkenlerini kullanın:

```html
<div class="bg-base-100 text-base-content">
  <!-- Tema renklerine uygun içerik -->
</div>
```

## HTMX ve Alpine.js Kullanımı

VivaCRM v2, interaktif arayüzler için HTMX ve Alpine.js kullanır.

### HTMX Örneği

```html
<button 
  hx-get="{% url 'customer:customer-detail' pk=customer.id %}" 
  hx-target="#customer-detail"
  hx-trigger="click"
  class="btn btn-primary"
>
  Müşteri Detayını Göster
</button>

<div id="customer-detail">
  <!-- HTMX yanıtı buraya yüklenecek -->
</div>
```

### Alpine.js Örneği

```html
<div x-data="{ open: false }">
  <button @click="open = !open" class="btn">
    Menüyü Aç/Kapat
  </button>
  
  <div x-show="open" x-transition class="mt-2 p-4 bg-base-200 rounded-md">
    Gizli içerik burada görünecek
  </div>
</div>
```

## Yeni Sayfa Ekleme Adımları

1. İlgili uygulama klasöründe gerekli view'i oluşturun
2. URL yapılandırmasını yapın
3. `templates/[app_name]/` dizininde şablon dosyasını oluşturun
4. Base şablonunu extend edin ve gerekli bileşenleri kullanın
5. Duyarlı tasarım ve tema desteğini kontrol edin

## Mevcut Şablonu Düzenleme Adımları

1. Şablon dosyasını bulun ve açın
2. Mevcut bileşenleri ve stili analiz edin
3. Gerekli değişiklikleri yapın, tutarlılığı koruyun
4. Değişikliklerinizi test edin (farklı ekran boyutları ve temalarda)

Bu rehber, VivaCRM v2 projesi için tutarlı ve kullanıcı dostu sayfalar oluşturmanıza yardımcı olacak temel prensipleri ve bileşenleri içerir. Yeni özellikler geliştirirken bu rehberi takip edin.