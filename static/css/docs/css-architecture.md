# VivaCRM CSS Architecture

## Dosya Yapısı

```
/static/css/
├── src/
│   ├── base/
│   │   ├── fonts.css        # Font yükleme stratejisi
│   │   ├── theme.css        # DaisyUI tema entegrasyonu
│   │   ├── typography.css   # Tipografi stilleri
│   │   └── variables.css    # CSS custom properties
│   ├── components/
│   │   ├── avatar.css       # Avatar component stilleri
│   │   ├── dashboard.css    # Dashboard özel stilleri
│   │   ├── menu.css         # Menu component stilleri
│   │   └── navbar.css       # Navbar component stilleri
│   ├── utilities/
│   │   ├── animations.css   # Animasyon utility'leri
│   │   ├── dark-mode.css    # Dark mode yönetimi
│   │   └── helpers.css      # Yardımcı utility sınıfları
│   ├── critical.css         # Above-the-fold CSS
│   ├── critical-optimized.css # Ultra optimized critical CSS
│   └── main.css             # Ana CSS entry point
└── dist/                    # Build output (gitignore'da)
```

## CSS Yazım Standartları

### 1. Import Sıralaması
```css
/* 1. Variables ve Base */
@import "./base/variables.css";
@import "./base/fonts.css";

/* 2. Tailwind Directives */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* 3. Theme */
@import "./base/theme.css";

/* 4. Components */
@import "./components/navbar.css";

/* 5. Utilities */
@import "./utilities/animations.css";
```

### 2. Component CSS Yapısı
```css
/**
 * Component Adı
 * Açıklama
 */

/* Base Styles */
.component-name {
  @apply base-tailwind-classes;
}

/* Variations */
.component-name--variant {
  @apply variant-classes;
}

/* States */
.component-name:hover {
  @apply hover-classes;
}

/* Responsive */
@media (max-width: 768px) {
  .component-name {
    @apply mobile-classes;
  }
}
```

### 3. Dark Mode Yönetimi
Tüm dark mode stilleri merkezi olarak `utilities/dark-mode.css` dosyasında yönetilir.

```css
[data-theme="vivacrmDark"] {
  .component {
    @apply dark-mode-styles;
  }
}
```

### 4. Animation Yönetimi
Tüm animasyonlar `utilities/animations.css` dosyasında tanımlanır.

```css
@keyframes animation-name {
  from { /* ... */ }
  to { /* ... */ }
}

.animate-custom {
  animation: animation-name duration timing;
}
```

## Best Practices

### 1. Tailwind First
- Önce Tailwind utility class'larını kullan
- Özel CSS sadece gerektiğinde yaz

### 2. No !important
- !important kullanmaktan kaçın
- Specificity sorunlarını doğru şekilde çöz

### 3. Component Scoping
- BEM naming convention kullan
- Component bazlı CSS organizasyonu

### 4. Performance
- Critical CSS inline olarak kullan
- Font loading strategy uygula
- PurgeCSS ile unused CSS'leri temizle

### 5. Maintainability
- CSS dosyalarını küçük tut
- Her dosyanın tek bir sorumluluğu olsun
- Değişkenleri merkezi olarak yönet

## Build Process

### Development
```bash
npm run css:dev
```

### Production
```bash
npm run css:build
```

### Watch Mode
```bash
npm run css:watch
```

## CSS Variables

### Renk Sistemi
```css
--viva-primary: theme(colors.green.600);
--viva-secondary: theme(colors.blue.600);
--viva-accent: theme(colors.amber.500);
```

### Spacing
```css
--viva-space-1: 0.25rem;
--viva-space-2: 0.5rem;
/* ... */
```

### Shadows
```css
--viva-shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
--viva-shadow-md: 0 4px 6px rgba(0,0,0,0.1);
/* ... */
```

## Font Loading Strategy

1. **Preload**: Critical font dosyalarını preload et
2. **Font Display**: `swap` kullan
3. **Fallback**: System font stack tanımla
4. **JavaScript**: Font yükleme durumunu kontrol et

```html
<link rel="preload" href="/static/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
```

## Dark Mode Implementation

1. CSS variables kullan
2. Theme switch için JavaScript
3. LocalStorage ile tercihi sakla
4. System preference detection

## Mobile First Approach

1. Base styles mobile için
2. Tablet ve desktop için media queries
3. Touch-friendly interactions
4. Performance optimization