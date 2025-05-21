# VivaCRM CSS Architecture

Modern CSS mimarisi ve build sistemi dökümentasyonu.

## 📁 Dosya Yapısı (ITCSS)

```
css/
├── src/                    # Kaynak CSS dosyaları
│   ├── 00-settings/        # Değişkenler ve sabitler
│   │   ├── _daisyui.css    # DaisyUI özelleştirmeleri
│   │   ├── _fonts.css      # Font tanımlamaları
│   │   └── _variables.css  # CSS değişkenleri
│   ├── 01-tools/           # Mixins ve fonksiyonlar
│   ├── 02-generic/         # Reset ve normalize
│   │   └── _theme.css      # Tema entegrasyonu
│   ├── 03-elements/        # HTML element stilleri
│   │   └── _typography.css # Tipografi stilleri
│   ├── 04-objects/         # Design patterns
│   ├── 05-components/      # UI bileşenleri
│   │   ├── _avatar.css     # Avatar component
│   │   ├── _card.css       # Card component
│   │   ├── _dashboard.css  # Dashboard stilleri
│   │   ├── _menu.css       # Menu component
│   │   └── _navbar.css     # Navbar component
│   ├── 06-themes/          # Tema özelleştirmeleri
│   │   └── _dark.css       # Dark mode stilleri
│   ├── 07-utilities/       # Yardımcı sınıflar
│   │   ├── _animations.css # Animasyonlar
│   │   └── _helpers.css    # Utility sınıflar
│   └── main.css            # Ana CSS dosyası
├── dist/                   # Build edilmiş dosyalar
│   ├── main.css            # Development CSS
│   └── main.min.css        # Production CSS (minified)
├── build.js                # PostCSS build scripti
├── dev-build.sh            # Development build script
├── package.json            # NPM bağımlılıkları
├── postcss.config.js       # PostCSS konfigürasyonu
└── test.html               # CSS test sayfası
```

## 🚀 Build Sistemleri

### Development Build
```bash
# Watch mode ile geliştirme
npm run dev

# Alternatif
./dev-build.sh
```

### Production Build
```bash
# Optimized ve minified build
npm run prod

# Alternatif
npm run build
```

### Test Build
```bash
# Tek seferlik build
npx tailwindcss -i ./src/main.css -o ./dist/main.css
```

## 🏗️ CSS Mimarisi (ITCSS)

ITCSS (Inverted Triangle CSS) metodolojisi kullanılmaktadır:

1. **Settings (00)**: 
   - CSS değişkenleri
   - Font tanımlamaları
   - DaisyUI özelleştirmeleri

2. **Tools (01)**: 
   - Mixins
   - Fonksiyonlar
   - (Şu an boş)

3. **Generic (02)**: 
   - Reset stilleri
   - Normalize
   - Tema entegrasyonu

4. **Elements (03)**: 
   - HTML element stilleri
   - Tipografi
   - Link stilleri

5. **Objects (04)**: 
   - Layout patterns
   - Grid sistemleri
   - (Şu an boş)

6. **Components (05)**: 
   - UI bileşenleri
   - Card, Avatar, Menu vb.
   - Dashboard özel stilleri

7. **Themes (06)**: 
   - Tema override'ları
   - Dark mode stilleri

8. **Utilities (07)**: 
   - Animasyonlar
   - Helper sınıflar
   - Tek amaçlı utility'ler

## 🛠️ Teknoloji Stack

- **Tailwind CSS 3.x**: Utility-first CSS framework
- **DaisyUI 4.x**: Tailwind CSS component library
- **PostCSS 8.x**: CSS işleme pipeline'ı
- **Autoprefixer**: Otomatik vendor prefix'ler
- **cssnano**: CSS minification
- **postcss-import**: CSS @import desteği
- **postcss-nested**: Nested CSS desteği

## 🎨 Tema Sistemi

### Mevcut Temalar
- `vivacrm`: Açık tema (varsayılan)
- `vivacrmDark`: Koyu tema

### Tema Kullanımı
```html
<!-- Açık tema -->
<html data-theme="vivacrm">

<!-- Koyu tema -->
<html data-theme="vivacrmDark">
```

### Tema Renkleri
- **Primary**: #22c55e (Yeşil)
- **Secondary**: #3b82f6 (Mavi)
- **Accent**: #f59e0b (Amber)
- **Error**: #ef4444 (Kırmızı)
- **Success**: #22c55e (Yeşil)
- **Warning**: #f59e0b (Amber)

## 📝 Geliştirme Rehberi

### Yeni Component Ekleme
1. `src/05-components/_yeni-component.css` dosyası oluştur
2. Component stillerini yaz (DaisyUI class'larını kullanabilirsin)
3. `main.css` dosyasında import et
4. Build işlemini çalıştır

### Best Practices
1. Component dosyaları `_` ile başlamalı
2. BEM naming convention takip edilmeli
3. DaisyUI class'ları öncelikli kullanılmalı
4. Custom utility'ler minimum tutulmalı
5. Dark mode desteği eklenmeli

### Kod Örneği
```css
/* Component tanımı */
.card {
  @apply bg-base-100 shadow-md rounded-box p-4;
  @apply transition-all duration-300 ease-in-out;
}

/* Component varyasyonları */
.card--stat {
  @apply bg-base-100 shadow-md rounded-box p-4;
}

/* Dark mode override */
[data-theme="vivacrmDark"] .card {
  @apply bg-base-200/80 border border-gray-700;
}
```

## 🐛 Hata Giderme

### Build Hataları
```bash
# Bağımlılıkları yeniden yükle
rm -rf node_modules package-lock.json
npm install

# Build cache'i temizle
rm -rf dist/*
npm run build
```

### CSS Görünmüyor
1. Django DEBUG modunu kontrol et
2. `python manage.py collectstatic` komutunu çalıştır
3. Browser cache'ini temizle (Ctrl+Shift+R)
4. Console'da 404 hatası var mı kontrol et

### DaisyUI Çalışmıyor
1. `tailwind.config.js` dosyasında plugin kontrolü
2. HTML'de `data-theme` attribute kontrolü
3. Build çıktısında DaisyUI class'larının varlığı

## 📊 Performance

### Optimizasyon Hedefleri
- Critical CSS: < 1KB (inline)
- Main CSS: < 30KB (gzipped)
- Build süresi: < 1s
- Watch mode gecikme: < 200ms

### Mevcut Metrikler
- Development build: ~72KB
- Production build: ~47KB
- Gzipped size: ~12KB
- Build süresi: ~100ms

## 🔗 Kaynaklar

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [DaisyUI Components](https://daisyui.com/components/)
- [PostCSS Plugins](https://www.postcss.parts/)
- [ITCSS Architecture](https://www.creativebloq.com/web-design/manage-large-css-projects-itcss-101517528)

## 📄 Lisans

Bu proje VivaCRM lisansı altındadır.