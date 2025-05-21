# VivaCRM CSS Performance Guide

## Build Optimizasyonları

### 1. CSS Minification
```bash
# Production build
npm run build:css:prod
```

### 2. PurgeCSS Kullanımı
PostCSS config'de PurgeCSS aktif:
- Kullanılmayan CSS'leri kaldırır
- Dosya boyutunu %90'a kadar azaltır
- Safelist'e önemli class'ları ekle

### 3. Critical CSS
```html
<!-- inline critical CSS -->
<style>
  /* critical.css içeriği */
</style>

<!-- async load main CSS -->
<link rel="preload" href="/static/css/dist/main.min.css" as="style">
<link rel="stylesheet" href="/static/css/dist/main.min.css" media="print" onload="this.media='all'">
```

## Performance Best Practices

### 1. Selector Performansı
```css
/* ❌ Kötü - çok spesifik */
body .container .sidebar .menu > li > a.active { }

/* ✅ İyi - düşük specificity */
.menu-link.active { }
```

### 2. Animation Optimization
```css
/* ❌ Kötü - layout değişimi */
.box {
  transition: width 0.3s;
}

/* ✅ İyi - transform kullan */
.box {
  transition: transform 0.3s;
  transform: scaleX(1.2);
}
```

### 3. will-change Kullanımı
```css
/* Animasyon öncesi */
.modal {
  will-change: transform, opacity;
}

/* Animasyon sonrası kaldır */
.modal.shown {
  will-change: auto;
}
```

### 4. CSS Containment
```css
/* Layout bağımsızlığı */
.card {
  contain: layout style;
}

/* Tam izolasyon */
.widget {
  contain: strict;
}
```

## Asset Optimization

### 1. Font Loading
```css
/* Font display swap */
@font-face {
  font-family: 'Inter var';
  font-display: swap;
  src: url('/fonts/inter-var.woff2') format('woff2');
}
```

### 2. Image Optimization
```css
/* WebP with fallback */
.hero {
  background-image: url('/images/hero.webp');
}

/* Fallback for older browsers */
.no-webp .hero {
  background-image: url('/images/hero.jpg');
}
```

### 3. CSS Loading Strategy
```html
<!-- Critical CSS inline -->
<style>/* critical styles */</style>

<!-- Main CSS preload -->
<link rel="preload" href="/css/main.css" as="style">

<!-- Component CSS lazy load -->
<link rel="stylesheet" href="/css/dashboard.css" media="print" onload="this.media='all'">
```

## Bundle Splitting

### 1. Route-based Splitting
```css
/* main.css - her sayfada */
@import "base/reset.css";
@import "base/variables.css";

/* dashboard.css - sadece dashboard'da */
@import "components/charts.css";
@import "components/widgets.css";
```

### 2. Media Query Splitting
```css
/* mobile.css */
@media (max-width: 768px) {
  /* Mobile styles */
}

/* desktop.css */
@media (min-width: 769px) {
  /* Desktop styles */
}
```

## Monitoring

### 1. CSS Stats
- File sizes
- Selector count
- Specificity graph
- Unused CSS percentage

### 2. Performance Metrics
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Cumulative Layout Shift (CLS)

### 3. Tools
- Chrome DevTools Coverage
- Lighthouse
- WebPageTest
- CSS Stats online tool

## Checklist

- [ ] Critical CSS inline edildi mi?
- [ ] Ana CSS async yükleniyor mu?
- [ ] Fontlar optimize edildi mi?
- [ ] Kullanılmayan CSS temizlendi mi?
- [ ] Animation'lar GPU-accelerated mı?
- [ ] Image'lar lazy load ediliyor mu?
- [ ] CSS dosyaları gzip'lendi mi?
- [ ] HTTP/2 push kullanılıyor mu?