# Frontend Geliştirme Adımları

## Kurulum

1. Node.js ve npm kurulumu (https://nodejs.org/en/download/)
2. Proje dizininde terminal açın
3. `npm install` komutu çalıştırılarak bağımlılıklar yüklenir

## Geliştirme

1. `npm run dev` komutu ile TailwindCSS geliştirme modunda çalıştırılır
2. Bu, CSS dosyalarınızı izleyecek ve değişikliklerinizi otomatik olarak derleyecektir
3. Uygulamanız üzerinde çalışırken, değişikliklerinizi anında görmek için bu komutu çalıştırın

## Derleme

1. Uygulamanızı canlıya almaya hazır olduğunuzda, `npm run build` komutu ile CSS dosyalarını derleyin ve optimize edin
2. Bu, CSS dosyalarınızı minify ederek sayfa yükleme süresini azaltır

## Klasör Yapısı

- `/static/css/src/` - Kaynak CSS dosyaları (TailwindCSS)
- `/static/css/dist/` - Derlenmiş CSS dosyaları
- `/static/js/src/` - Kaynak JavaScript dosyaları
- `/static/js/lib/` - JavaScript kütüphaneleri (HTMX, Alpine.js, vb.)
- `/static/js/dist/` - Derlenmiş JavaScript dosyaları
- `/static/img/` - Görsel dosyaları
- `/static/fonts/` - Font dosyaları

## Kullanılan Teknolojiler

### TailwindCSS
- Hızlı bir şekilde duyarlı web siteleri tasarlamak için kullanılan bir CSS framework
- Belge: https://tailwindcss.com/docs

### DaisyUI
- TailwindCSS üzerine kurulu komponentler kütüphanesi
- Belge: https://daisyui.com/docs/

### Alpine.js
- Minimal ve basit bir JavaScript framework
- Deklaratif yöntemlerle DOM manipülasyonu sağlar
- Belge: https://alpinejs.dev/

### HTMX
- AJAX, CSS Transitions, WebSockets ve Server Sent Events gibi modern tarayıcı özelliklerini direkt olarak HTML içinde kullanmanızı sağlar
- Belge: https://htmx.org/docs/

## Tema Ayarları

TailwindCSS ve DaisyUI ile iki farklı tema oluşturulmuştur:
- `vivacrm` - Açık tema (varsayılan)
- `vivacrmDark` - Koyu tema

Tema değiştirme butonu sayesinde kullanıcılar açık ve koyu tema arasında geçiş yapabilirler. Kullanıcı tercihi localStorage içinde saklanır.

## HTMX Kullanımı

HTMX, sayfa yenilemesi olmadan backend ile etkileşim kurmanızı sağlar.

Örnek:
```html
<button 
  hx-post="/api/users/1/activate" 
  hx-target="#user-status" 
  hx-swap="outerHTML"
  hx-indicator="#loading"
>
  Aktif Et
</button>
<div id="loading" class="htmx-indicator">
  Yükleniyor...
</div>
```

## Alpine.js Kullanımı

Alpine.js, sayfa üzerinde reaktif komponentler oluşturmanızı sağlar.

Örnek:
```html
<div x-data="{ open: false }">
  <button @click="open = !open">Menu</button>
  <div x-show="open">
    Menu içeriği
  </div>
</div>
```

## Form Doğrulama

Form doğrulaması için Django form doğrulama sistemi kullanılmaktadır. Frontend tarafında Alpine.js ve HTML5 form doğrulamaları destekleyici olarak kullanılır.

## Responsive Tasarım

Tüm sayfalar responsive olarak tasarlanmıştır. Farklı ekran boyutlarında uygun görünüm için TailwindCSS sınıfları kullanılmıştır.

En yaygın kullanılan ekran boyutu sınıfları:
- `sm`: >= 640px
- `md`: >= 768px
- `lg`: >= 1024px
- `xl`: >= 1280px
- `2xl`: >= 1536px