# VivaCRM Bileşen Kütüphanesi

Bu doküman, VivaCRM v2 uygulamasında kullanılan bileşenleri (components) açıklar ve nasıl kullanılacağı hakkında örnekler sunar.

## İçindekiler

1. [Giriş](#giriş)
2. [Kart (Card)](#kart-card)
3. [Veri Tablosu (Data Table)](#veri-tablosu-data-table)
4. [Form](#form)
5. [İstatistik Kartı (Stats Card)](#i̇statistik-kartı-stats-card)
6. [Modal](#modal)
7. [Uyarı (Alert)](#uyarı-alert)
8. [Sekmeler (Tabs)](#sekmeler-tabs)
9. [Rozet (Badge)](#rozet-badge)
10. [Ekmek Kırıntısı (Breadcrumb)](#ekmek-kırıntısı-breadcrumb)
11. [Boş Durum (Empty State)](#boş-durum-empty-state)
12. [Açılır Menü (Dropdown)](#açılır-menü-dropdown)
13. [İpucu (Tooltip)](#i̇pucu-tooltip)
14. [Sayfalama (Pagination)](#sayfalama-pagination)

## Giriş

VivaCRM v2, DaisyUI üzerine kurulu özel bir bileşen kütüphanesi kullanır. Bu bileşenler, kullanıcı arayüzünde tutarlılık sağlar ve geliştirme sürecini hızlandırır.

Bileşenleri kullanmak için Django şablonlarında `include` etiketini kullanırız:

```html
{% include "components/BILEŞEN_ADI.html" with PARAMETRE1=DEĞER1 PARAMETRE2=DEĞER2 %}
```

## Kart (Card)

Temel içerik bileşeni.

### Kullanım

```html
{% include "components/card.html" with 
  title="Kart Başlığı"
  subtitle="Alt Başlık (Opsiyonel)"
  class="w-full md:w-1/2"
  collapsible=True
  collapsed=False
%}
  {% block content %}
    Kart içeriği buraya gelecek
  {% endblock %}
  
  {% block actions %}
    <button class="btn btn-primary">Tamam</button>
    <button class="btn btn-ghost">İptal</button>
  {% endblock %}
{% include "components/card.html" %}
```

### Parametreler

- `title`: Kart başlığı
- `subtitle`: Alt başlık (opsiyonel)
- `image`: Kart resmi URL'si (opsiyonel)
- `class`: Ek CSS sınıfları (opsiyonel)
- `collapsible`: Katlanabilir kart (opsiyonel, boolean)
- `collapsed`: Başlangıçta katlanmış durumda (opsiyonel, boolean)
- `is_hoverable`: Hover efekti (opsiyonel, boolean)
- `border_color`: Kenarlık rengi (opsiyonel, örn: "primary", "success")
- `id`: Kart için benzersiz ID (opsiyonel)

### Bloklar

- `content`: Kart içeriği
- `actions`: İşlem butonları
- `header_actions`: Başlıkta gösterilecek ek işlemler

## Veri Tablosu (Data Table)

HTMX ve Alpine.js ile güçlendirilmiş gelişmiş veri tablosu bileşeni.

### Kullanım

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

### Parametreler

- `objects`: Gösterilecek nesnelerin listesi
- `columns`: Gösterilecek sütunlar (virgülle ayrılmış)
- `headers`: Sütun başlıkları (virgülle ayrılmış)
- `actions`: İşlem butonlarını göster (opsiyonel, boolean)
- `title`: Tablo başlığı
- `add_url`: Yeni kayıt ekleme URL'si (opsiyonel)
- `detail_url_name`: Detay sayfası URL adı (opsiyonel)
- `edit_url_name`: Düzenleme sayfası URL adı (opsiyonel)
- `delete_url_name`: Silme işlemi URL adı (opsiyonel)
- `empty_message`: Veri yokken gösterilecek mesaj (opsiyonel)
- `select`: Satır seçimi özelliği (opsiyonel, boolean)
- `bulk_actions`: Toplu işlemler (opsiyonel, dict)
- `sortable_columns`: Sıralanabilir sütunlar (opsiyonel, liste)
- `target`: HTMX hedefi (opsiyonel)

## Form

HTMX ve Alpine.js ile güçlendirilmiş form bileşeni.

### Kullanım

```html
{% include "components/form.html" with 
  form=form 
  url="/path/to/submit" 
  method="post" 
  title="Form Başlığı" 
  submit_text="Kaydet" 
  cancel_url="customers:customer-list"
%}
```

### Parametreler

- `form`: Django form nesnesi
- `url`: Form gönderilecek URL
- `method`: HTTP metodu (post, put, vb.)
- `title`: Form başlığı (opsiyonel)
- `submit_text`: Gönderme butonu metni (opsiyonel)
- `cancel_url`: İptal butonu URL'si (opsiyonel)
- `enctype`: Form enctype özelliği (opsiyonel)
- `id`: Form için benzersiz ID (opsiyonel)
- `success_message`: Başarı mesajı (opsiyonel)
- `target`: HTMX hedefi (opsiyonel)
- `confirm`: Onay mesajı (opsiyonel)

## İstatistik Kartı (Stats Card)

İstatistikleri görsel olarak göstermek için kullanılan kart bileşeni.

### Kullanım

```html
{% include "components/stats_card.html" with 
  title="Toplam Müşteri"
  value=total_customers
  icon="users"
  color="primary"
  percent=10
  trend="up"
  period="Bu ay"
%}
```

### Parametreler

- `title`: Kart başlığı
- `value`: Gösterilecek değer
- `icon`: İkon adı (users, box, file, cart, money, chart, check, alert)
- `color`: Renk (primary, secondary, accent, info, success, warning, error)
- `percent`: Yüzde değişim (opsiyonel)
- `trend`: Değişim trendi (up, down veya boş, opsiyonel)
- `period`: Zaman aralığı (opsiyonel)
- `link_url`: Detay bağlantı URL'si (opsiyonel)
- `link_text`: Detay bağlantı metni (opsiyonel)
- `show_chart`: Mini grafik göster (opsiyonel, boolean)

## Modal

Alpine.js ile güçlendirilmiş modal bileşeni.

### Kullanım

```html
{% include "components/modal.html" with 
  id="example-modal"
  title="Modal Başlığı"
  content="Modal içeriği buraya gelecek."
  cancel_text="İptal"
  confirm_text="Tamam"
  confirm_class="btn-primary"
%}
```

JavaScript ile açmak için:
```javascript
document.getElementById('example-modal').dispatchEvent(new CustomEvent('open-modal'))
```

HTMX ile açmak için:
```html
<button hx-get="/api/some-endpoint" 
        hx-target="#modal-content" 
        hx-trigger="click" 
        hx-on::after-request="document.getElementById('example-modal').dispatchEvent(new CustomEvent('open-modal'))">
  Modal Aç
</button>
```

### Parametreler

- `id`: Modal için benzersiz ID
- `title`: Modal başlığı (opsiyonel)
- `content`: Modal içeriği (opsiyonel)
- `cancel_text`: İptal butonu metni (opsiyonel)
- `confirm_text`: Onay butonu metni (opsiyonel)
- `cancel_class`: İptal butonu CSS sınıfı (opsiyonel)
- `confirm_class`: Onay butonu CSS sınıfı (opsiyonel)
- `close_button`: Kapatma ikonu göster (opsiyonel, boolean)
- `backdrop_close`: Arka plan tıklamasıyla kapat (opsiyonel, boolean)
- `confirm_js`: Onay işlevi JavaScript kodu (opsiyonel)

## Uyarı (Alert)

Kullanıcıya bilgi vermek için kullanılan uyarı bileşeni.

### Kullanım

```html
{% include "components/alert.html" with 
  type="success" 
  message="İşlem başarıyla tamamlandı."
  icon=True
  dismissible=True 
%}
```

### Parametreler

- `type`: Uyarı tipi (info, success, warning, error)
- `message`: Uyarı mesajı
- `icon`: İkon göster (opsiyonel, boolean)
- `dismissible`: Kapatılabilir (opsiyonel, boolean)
- `class`: Ek CSS sınıfları (opsiyonel)

## Sekmeler (Tabs)

İçeriği sekmeler halinde düzenlemek için kullanılan bileşen.

### Kullanım

```html
{% include "components/tabs.html" with 
  id="example-tabs"
  tabs="Genel Bilgiler,İletişim,Adresler,Siparişler"
  initial_tab=0
%}
  {% block tab_0 %}
    Genel Bilgiler içeriği buraya gelecek
  {% endblock %}
  
  {% block tab_1 %}
    İletişim içeriği buraya gelecek
  {% endblock %}
  
  {% block tab_2 %}
    Adresler içeriği buraya gelecek
  {% endblock %}
  
  {% block tab_3 %}
    Siparişler içeriği buraya gelecek
  {% endblock %}
{% include "components/tabs.html" %}
```

### Parametreler

- `id`: Sekmeler için benzersiz ID (opsiyonel)
- `tabs`: Sekme başlıkları (virgülle ayrılmış)
- `initial_tab`: Başlangıçta aktif sekme indeksi (opsiyonel, varsayılan: 0)
- `class`: Ek CSS sınıfları (opsiyonel)

### Bloklar

Her sekme için ayrı blok kullanılır: `tab_0`, `tab_1`, `tab_2`, vb.

## Rozet (Badge)

Durum göstergeleri ve etiketler için kullanılan küçük rozet bileşeni.

### Kullanım

```html
{% include "components/badge.html" with 
  text="Tamamlandı"
  type="success"
  size="md"
  icon="check"
%}
```

### Parametreler

- `text`: Rozet metni
- `type`: Rozet tipi (primary, secondary, accent, info, success, warning, error, neutral)
- `size`: Boyut (sm, md, lg, opsiyonel)
- `icon`: İkon adı (check, alert, info, clock, x, opsiyonel)
- `class`: Ek CSS sınıfları (opsiyonel)

## Ekmek Kırıntısı (Breadcrumb)

Navigasyon bileşeni.

### Kullanım

```html
{% include "components/breadcrumb.html" with 
  items="Anasayfa:dashboard:dashboard,Müşteriler:customers:customer-list,Müşteri Detayı:"
%}
```

### Parametreler

- `items`: Ekmek kırıntısı öğeleri (virgülle ayrılmış)
  Format: "Etiket:url_name:url_param,Etiket2:url_name2:,..."
- `class`: Ek CSS sınıfları (opsiyonel)

## Boş Durum (Empty State)

Veri olmadığında kullanıcıyı bilgilendirmek için kullanılan bileşen.

### Kullanım

```html
{% include "components/empty_state.html" with 
  title="Hiç müşteri bulunamadı"
  message="Henüz hiç müşteri kaydı oluşturulmamış."
  action_text="Müşteri Ekle"
  action_url="customers:customer-create"
  icon="users"
%}
```

### Parametreler

- `title`: Başlık
- `message`: Açıklama metni
- `action_text`: İşlem butonu metni (opsiyonel)
- `action_url`: İşlem butonu URL'si (opsiyonel)
- `action_icon`: İşlem butonunda ikon göster (opsiyonel, boolean)
- `icon`: İkon adı (users, box, file, cart, money, chart, search, settings)
- `class`: Ek CSS sınıfları (opsiyonel)

## Açılır Menü (Dropdown)

Açılır menü bileşeni.

### Kullanım

```html
{% include "components/dropdown.html" with 
  id="user-menu"
  button_text="İşlemler"
  button_icon="menu"
  button_class="btn-primary"
  items="Profil:users:user-profile,Ayarlar:settings:user-settings,Çıkış Yap:accounts:logout"
  position="dropdown-end"
%}
```

veya:

```html
{% include "components/dropdown.html" with button_text="İşlemler" %}
  {% block content %}
    <li><a href="{% url 'users:user-profile' %}">Profil</a></li>
    <li><a href="{% url 'settings:user-settings' %}">Ayarlar</a></li>
    <li><a href="{% url 'accounts:logout' %}">Çıkış Yap</a></li>
  {% endblock %}
{% include "components/dropdown.html" %}
```

### Parametreler

- `id`: Benzersiz ID (opsiyonel)
- `button_text`: Buton metni (opsiyonel)
- `button_icon`: Buton ikonu (menu, user, settings, dots, plus, filter, opsiyonel)
- `button_class`: Buton CSS sınıfı (opsiyonel)
- `items`: Menü öğeleri (virgülle ayrılmış)
  Format: "Etiket:url_name:url_param,Etiket2:url_name2:,..."
- `position`: Pozisyon (dropdown-end, dropdown-left, dropdown-right, dropdown-top, dropdown-bottom, opsiyonel)
- `class`: Ek CSS sınıfları (opsiyonel)

### Bloklar

- `content`: Özel menü içeriği

## İpucu (Tooltip)

Elemanlara ipucu ekleme bileşeni.

### Kullanım

```html
{% include "components/tooltip.html" with 
  text="Bu bir ipucu metnidir"
  position="tooltip-top"
%}
  <button class="btn">Butonun Üzerine Gelin</button>
{% include "components/tooltip.html" %}
```

### Parametreler

- `text`: İpucu metni
- `position`: Pozisyon (tooltip-top, tooltip-bottom, tooltip-left, tooltip-right, opsiyonel)
- `class`: Ek CSS sınıfları (opsiyonel)

## Sayfalama (Pagination)

Sayfalama bileşeni.

### Kullanım

```html
{% include "components/pagination.html" with 
  objects=page_obj
  size="md"
  query_params=request.GET
  target="#content-area"
%}
```

### Parametreler

- `objects`: Paginator nesnesi 
- `size`: Buton boyutu (sm, md, lg, opsiyonel)
- `query_params`: Sorgu parametreleri (opsiyonel)
- `target`: HTMX hedefi (opsiyonel)
- `class`: Ek CSS sınıfları (opsiyonel)