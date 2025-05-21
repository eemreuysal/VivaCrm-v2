/**
 * VivaCRM - Alpine.js Unified Modular Initialization
 * 
 * Bu dosya, yeni modüler yapıyı kullanan ana başlatma noktasıdır.
 * ES modülleri ile Alpine.js bileşenlerini, store'larını ve yardımcılarını
 * modüler ve bakımı kolay bir şekilde başlatır.
 * 
 * Geriye dönük uyumluluk için eski global API'yi de sağlar.
 */

import { initializeAlpine, reinitializeAlpineNode } from './core/alpine-init.js';
import { formatters } from './core/utils.js';

// Global namespace oluştur
window.VivaCRM = window.VivaCRM || {};

// Sayfa türünü otomatik olarak tespit et
function detectPageType() {
  const path = window.location.pathname;
  
  if (path.includes('/dashboard')) {
    return 'dashboard';
  } else if (path.includes('/accounts/login') || path.includes('/accounts/register')) {
    return 'auth';
  } else if (path.includes('/products')) {
    return 'products';
  } else if (path.includes('/customers')) {
    return 'customers';
  } else if (path.includes('/orders')) {
    return 'orders';
  } else if (path.includes('/invoices')) {
    return 'invoices';
  }
  
  return null;
}

// Alpine.js'i başlat
async function init() {
  // Başlatma seçenekleri
  const options = {
    pageType: detectPageType(),
    formatters: formatters,
    setupHtmx: true
  };
  
  // Alpine.js'i başlat
  await initializeAlpine(options);
}

// Sayfa durumuna göre başlat
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Global API
window.VivaCRM.Alpine = window.VivaCRM.Alpine || {};
window.VivaCRM.Alpine.initialize = initializeAlpine;
window.VivaCRM.Alpine.reinitializeNode = reinitializeAlpineNode;

// Temiz modüler API'yi dışa aktar
export {
  initializeAlpine,
  reinitializeAlpineNode
};