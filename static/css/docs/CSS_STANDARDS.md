# VivaCRM v2 CSS Standardları ve Yapısı

Bu doküman, VivaCRM v2 projesindeki CSS yapılandırmasını, kod düzenini ve tema yönetimini açıklamaktadır.

## İçindekiler

1. [CSS Mimari Yapısı](#css-mimari-yapısı)
2. [Dosya Organizasyonu](#dosya-organizasyonu)
3. [Tema Sistemi](#tema-sistemi)
4. [Bileşen CSS Yapısı](#bileşen-css-yapısı)
5. [Kritik CSS Yapısı](#kritik-css-yapısı)
6. [Geliştirme Standartları](#geliştirme-standartları)
7. [CSS Performans Optimizasyonları](#css-performans-optimizasyonları)

## CSS Mimari Yapısı

VivaCRM v2, "ITCSS" (Inverted Triangle CSS) metodolojisini kullanarak CSS dosyalarını organize eder. Bu yapı, spesifiklik (specificity) kontrolünü iyileştirir ve CSS dosyalarının düzenli kalmasını sağlar.

### ITCSS Katmanları

1. **Settings**: Değişkenler, tema tanımları, genel ayarlar
2. **Tools**: Mixinler ve fonksiyonlar
3. **Generic**: Reset/normalize stilleri
4. **Elements**: HTML elementlerinin temel stilleri
5. **Objects**: Tasarım kalıpları (layout, grid, vb.)
6. **Components**: UI bileşenleri
7. **Themes**: Tema varyasyonları
8. **Utilities**: Yardımcı sınıflar

## Dosya Organizasyonu

CSS dosyaları aşağıdaki yapıda organize edilmiştir:

```
/static/css/
├── critical-standardized.css           # Kritik CSS (head içine inline)
├── src/
│   ├── main-standardized.css           # Ana CSS giriş noktası
│   ├── 00-settings/                    # Değişkenler ve ayarlar
│   │   ├── _variables-standardized.css # CSS değişkenleri
│   │   ├── _fonts.css                  # Font tanımları
│   │   └── _daisyui.css                # DaisyUI tema tanımları
│   ├── 01-tools/                       # Mixinler (gelecekte kullanılacak)
│   ├── 02-generic/                     # Reset/normalize stilleri
│   │   └── _theme-transition-standardized.css # Tema geçiş stilleri
│   ├── 03-elements/                    # HTML elementleri
│   │   └── _typography.css             # Tipografi stilleri
│   ├── 04-objects/                     # Yapısal kalıplar (gelecekte kullanılacak)
│   ├── 05-components/                  # UI bileşenleri
│   │   ├── _navbar-standardized.css    # Navbar bileşeni
│   │   ├── _sidebar-standardized.css   # Sidebar bileşeni
│   │   ├── _card.css                   # Card bileşeni
│   │   └── ...                         # Diğer bileşenler
│   ├── 06-themes/                      # Tema varyasyonları
│   │   └── _dark-standardized.css      # Koyu tema özellikleri
│   └── 07-utilities/                   # Yardımcı sınıflar
│       ├── _animations.css             # Animasyon sınıfları
│       ├── _effects-standardized.css   # Görsel efektler
│       └── _helpers.css                # Çeşitli yardımcı sınıflar
└── docs/
    └── CSS_STANDARDS.md                # Bu doküman
```

## Tema Sistemi

VivaCRM v2, hem açık hem de koyu temayı destekler. Tema sistemi CSS değişkenleri, DaisyUI ve TailwindCSS ile entegre çalışır.

### Tema Değişkenleri

Tema değişkenleri `_variables-standardized.css` dosyasında tanımlanmıştır:

```css
:root {
  /* Marka Renkleri */
  --viva-primary-500: #22c55e;
  --viva-secondary-500: #3b82f6;
  --viva-accent-500: #f59e0b;
  
  /* DaisyUI Tema Değişkenleri */
  --p: 142 71% 45%;  /* Primary - Green */
  --s: 217 91% 60%;  /* Secondary - Blue */
  /* vs diğer tema değişkenleri */
}

[data-theme="vivacrmDark"] {
  /* Koyu Tema Değişkenleri */
  --b1: 220 18% 14%;  /* Base 100 */
  --b2: 220 17% 11%;  /* Base 200 */
  /* vs diğer koyu tema değişkenleri */
}
```

### Tema Geçişleri

Tema değişiklikleri sırasında yumuşak geçişler `_theme-transition-standardized.css` ile sağlanır:

```css
/* Tema Geçişleri */
html.theme-transition,
html.theme-transition * {
  transition-property: background-color, border-color, color, fill, stroke;
  transition-duration: 300ms;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Tema Yönetimi

Tema yönetimi, JavaScript tarafında `theme-manager-standardized.js` ile gerçekleştirilir:

```javascript
// Tema değiştirme
themeManager.toggleTheme();

// Sistem tercihine uyum
themeManager.useSystemPreference();
```

## Bileşen CSS Yapısı

Bileşen CSS dosyaları standart bir format izler ve birden fazla ilgisiz dosyanın oluşmasını önler:

### Dosya Adlandırması

- Tüm bileşen dosyaları alt çizgi (_) ile başlar: `_navbar.css`
- İlgili yardımcı sınıflar doğru utility dosyasına taşınır
- Animasyonlar `_animations.css` içinde saklanır

### CSS Organizasyonu

Bir bileşen CSS dosyası şu yapıda düzenlenmelidir:

```css
/**
 * Bileşen Açıklaması
 */

/* Temel Konteyner */
.component {
  @apply ...; /* Temel stiller */
}

/* Alt Elementler */
.component-header {
  @apply ...;
}

/* Durumlar */
.component.active {
  @apply ...;
}

/* Medya Sorguları */
@media (max-width: 640px) {
  .component {
    @apply ...;
  }
}
```

## Kritik CSS Yapısı

Kritik CSS, sayfa ilk yüklendiğinde görünen içeriğin stillerini optimize eder ve sayfa render performansını artırır.

### Kritik CSS İçeriği

- Minimum gerekli reset
- Tema değişkenleri
- Temel layout stilleri
- FOUC (Flash of Unstyled Content) önleme

### Kullanımı

Kritik CSS, sayfa head bölümünde inline olarak yüklenir:

```html
<head>
  <style>
    /* critical-standardized.css içeriği */
  </style>
</head>
```

## Geliştirme Standartları

### CSS Yazım Kuralları

1. **Sınıf İsimlendirme**: kebab-case kullanılır (ör. `card-header`)
2. **BEM Metodolojisi**: Gerekli durumlarda BEM notasyonu kullanılır:
   ```css
   .block {}
   .block__element {}
   .block--modifier {}
   ```
3. **TailwindCSS**: Komponente özel stiller için `@apply` kullanılır
4. **Açıklamalar**: Her dosyanın başında açıklama ve her büyük bölüm başlangıcı belirtilir
5. **Boşluklar**: Okunabilirlik için ilgili bölümler arasında boş satır bırakılır

### Stil Uygulama Hiyerarşisi

1. **Base Styles**: Tüm uygulamada geçerli temel stiller
2. **Component Styles**: Bileşene özel stiller
3. **Theme Overrides**: Tema-spesifik değişiklikler
4. **State/Modifier Styles**: Durum-spesifik stiller
5. **Utility Classes**: Yardımcı sınıflar

## CSS Performans Optimizasyonları

### Kritik CSS İnline Etme

Sayfa yükleme süresini iyileştirmek için kritik CSS inline edilir:

```html
<style>
  /* critical.css */
</style>
```

### Lazy-Loading CSS

Kritik olmayan CSS dosyaları sayfa performansını artırmak için geciktirilir:

```html
<link rel="preload" href="/css/main.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="/css/main.css"></noscript>
```

### Seçici Optimizasyonu

- Aşırı spesifiklikten kaçının
- Gereksiz yere uzun seçiciler kullanmaktan kaçının
- Performans için gereksiz seçicilerden kaçının

### FOUC Önlemi

Flash of Unstyled Content önlemek için:

```css
html.no-js {
  visibility: hidden;
}
```

```javascript
document.addEventListener('DOMContentLoaded', () => {
  document.documentElement.classList.remove('no-js');
});
```

## Teşekkürler

Bu standartlar, kodun tutarlılığını sağlamak ve VivaCRM v2 CSS yapısını güçlendirmek için geliştirilmiştir. Sorularınız veya önerileriniz varsa, geliştirme ekibiyle iletişime geçiniz.

---

_Son Güncelleme: 21.05.2025_