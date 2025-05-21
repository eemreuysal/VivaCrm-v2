/**
 * VivaCRM v2 - Alpine.js Başlatma
 * 
 * Bu dosya, yeni ve temiz core/alpine-init.js'e yönlendirme yapar.
 * Geriye dönük uyumluluk için kullanılmaktadır.
 */

import alpineInit from './core/alpine-init.js';

// Modülü dışa aktar
export default alpineInit;

// Sayfa yükleme durumunu kontrol et ve uygun şekilde başlat
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', alpineInit.initialize);
} else {
  alpineInit.initialize();
}