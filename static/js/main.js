/**
 * VivaCRM v2 Ana Giriş Noktası
 * 
 * Bu dosya, uygulama başlangıç noktasıdır ve tüm bileşenlerin kaydını yapar,
 * üçüncü parti kütüphaneleri başlatır ve genel yapılandırmayı gerçekleştirir.
 * 
 * @module main
 */

// Üçüncü parti kütüphaneleri içe aktar
import Alpine from 'alpinejs';
import htmx from 'htmx.org';

// Store'ları içe aktar
import { registerStores } from './stores';

// Dashboard Modülü Bileşenleri
import { dashboardComponent } from './components/dashboard'; 
import { ordersTableApp } from './components/dashboard-components';

// Yardımcı Modüller
import * as formatters from './utils/formatters';

// HTMX konfigürasyonu (yan etkili import)
import './utils/htmx-config';

// Global olarak Alpine'ı erişilebilir yap (geliştirme için)
window.Alpine = Alpine;

/**
 * Yardımcı fonksiyonları Alpine.js'e kaydet
 */
function registerMagicHelpers() {
  // Format yardımcıları
  Alpine.magic('formatDate', () => formatters.formatDate);
  Alpine.magic('formatCurrency', () => formatters.formatCurrency);
  Alpine.magic('formatNumber', () => formatters.formatNumber);
  
  console.info('Alpine.js magic helpers registered');
}

/**
 * Komponentleri Alpine.js'e kaydet
 */
function registerComponents() {
  // Dashboard komponentleri
  Alpine.data('dashboardComponent', dashboardComponent);
  Alpine.data('ordersTableApp', ordersTableApp);
  
  console.info('Alpine.js components registered');
}

/**
 * Ana init fonksiyonu - uygulama başlangıç noktası
 */
function initApp() {
  // HTMX global nesnesini erişilebilir yap
  window.htmx = htmx;
  
  // Store'ları kaydet
  registerStores(Alpine);
  
  // Magic yardımcıları kaydet
  registerMagicHelpers();
  
  // Komponentleri kaydet
  registerComponents();
  
  // Alpine'ı başlat
  Alpine.start();
  
  console.info('VivaCRM application initialized successfully');
  
  // Olay dinleyicileri ve diğer başlangıç işlemleri
  document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.classList.remove('no-js');
    document.documentElement.classList.add('js-loaded');
    
    // Site yüklendi olayını tetikle
    document.dispatchEvent(new CustomEvent('vivacrm:app-loaded'));
  });
}

// Uygulamayı başlat
initApp();