/**
 * VivaCRM - HTMX Alpine.js Bridge
 * 
 * Bu modül, HTMX ve Alpine.js arasındaki entegrasyonu sağlar.
 * HTMX içerik güncellemelerinden sonra Alpine.js bileşenlerinin
 * doğru şekilde yeniden başlatılmasını garanti eder.
 */

import { createLogger, waitForElement, debounce } from './utils.js';

// Modül için logger oluştur
const logger = createLogger('HTMX-Alpine', {
  emoji: '🔄'
});

/**
 * Alpine.js bileşenlerinin state'ini korumak için kullanılan önbellek
 * @type {Map}
 */
const stateCache = new Map();

/**
 * HTMX ve Alpine.js arasındaki entegrasyonu kurar.
 * Tüm HTMX olaylarını dinler ve gerektiğinde Alpine.js bileşenlerini 
 * yeniden başlatır.
 */
export function setupHtmxIntegration() {
  logger.info('HTMX-Alpine entegrasyonu başlatılıyor...');
  
  // Alpine.js ve HTMX'in yüklü olup olmadığını kontrol et
  if (typeof window.Alpine === 'undefined') {
    logger.error('Alpine.js yüklü değil! Entegrasyon kurulamadı.');
    return false;
  }
  
  // Sayfa yükleme durumunu kontrol et
  if (!document.body) {
    logger.warn('document.body henüz hazır değil, DOMContentLoaded olayını bekliyoruz...');
    document.addEventListener('DOMContentLoaded', () => setupHtmxIntegration());
    return false;
  }

  // HTMX yüklü mü kontrol et - window.htmx veya DOM'da data-hx-* olan elementler
  const htmxExists = typeof window.htmx !== 'undefined' || 
                     document.querySelector('[data-hx-get], [data-hx-post], [data-hx-put], [data-hx-delete], [hx-get], [hx-post], [hx-put], [hx-delete]');
  
  if (!htmxExists) {
    logger.warn('HTMX yüklü değil veya hiçbir HTMX özniteliği bulunamadı. Entegrasyon kuruldu ama etkin olmayacak.');
  }

  // ---- HTMX Olay Dinleyicileri ----

  // HTMX içerik değişikliği başlamadan önce işlemler
  document.body.addEventListener('htmx:beforeSwap', function(event) {
    const target = event.detail.target;
    
    // Hedef bileşende Alpine.js durum var mı kontrol et
    if (target) {
      saveAlpineState(target);
    }
  });

  // HTMX içerik değişikliğinden sonra Alpine.js bileşenlerini yeniden başlat
  document.body.addEventListener('htmx:afterSwap', function(event) {
    const swappedNode = event.detail.target;
    
    // Alpine.js bileşenleri içeriyor mu kontrol et
    if (hasAlpineComponents(swappedNode)) {
      logger.debug('HTMX sonrası Alpine.js bileşenleri tespit edildi, yeniden başlatılıyor');
      
      // Güvenlik için küçük bir gecikme ekle
      setTimeout(() => {
        initializeAlpineComponents(swappedNode);
        restoreAlpineState(swappedNode);
      }, 10);
    }
  });
  
  // HTMX ajax sorgusu tamamlandığında 
  document.body.addEventListener('htmx:afterRequest', function(event) {
    // Sadece hata durumunda loglama yap
    if (event.detail.failed) {
      logger.warn(`HTMX isteği başarısız: ${event.detail.xhr?.status} ${event.detail.xhr?.statusText}`);
    }
  });
  
  // HTMX sayfa yüklemesi tamamlandığında
  document.body.addEventListener('htmx:load', function(event) {
    const loadedNode = event.detail.elt;
    
    // Alpine.js bileşenleri içeriyor mu kontrol et
    if (hasAlpineComponents(loadedNode)) {
      logger.debug('HTMX load sonrası Alpine.js bileşenleri tespit edildi');
      initializeAlpineComponents(loadedNode);
    }
  });
  
  // HTMX içerik geçişi sırasında hata oluştuğunda
  document.body.addEventListener('htmx:responseError', function(event) {
    logger.error(`HTMX yanıt hatası: ${event.detail.error}`);
  });

  logger.info('HTMX-Alpine entegrasyonu başarıyla kuruldu');
  return true;
}

/**
 * Belirtilen DOM düğümünde Alpine.js bileşeni olup olmadığını kontrol eder
 * 
 * @param {Element} node - Kontrol edilecek DOM düğümü
 * @returns {boolean} - Alpine.js bileşeni varsa true, yoksa false
 */
function hasAlpineComponents(node) {
  if (!node) return false;
  
  // Node'un kendisinde x-data özniteliği var mı
  if (node.hasAttribute && node.hasAttribute('x-data')) {
    return true;
  }
  
  // Alt elementlerde x-data özniteliği var mı
  return !!node.querySelector('[x-data]');
}

/**
 * Belirtilen DOM düğümündeki tüm Alpine.js bileşenlerini başlatır
 * 
 * @param {Element} node - Alpine.js bileşenlerini içeren DOM düğümü
 * @returns {boolean} - Başarılı olursa true, olmazsa false
 */
function initializeAlpineComponents(node) {
  if (!node || !window.Alpine) return false;
  
  try {
    // Alpine.initTree metodunun varlığını kontrol et
    if (typeof Alpine.initTree === 'function') {
      Alpine.initTree(node);
      logger.debug('Alpine.js bileşenleri başarıyla başlatıldı');
      return true;
    } else {
      logger.error('Alpine.initTree metodu bulunamadı! Alpine.js sürümünüzü kontrol edin.');
      return false;
    }
  } catch (error) {
    logger.error(`Alpine.js başlatma hatası: ${error.message}`);
    console.error(error);
    return false;
  }
}

/**
 * Bir DOM düğümündeki Alpine.js bileşenlerinin durumunu kaydeder
 * 
 * @param {Element} node - Alpine.js bileşenlerini içeren DOM düğümü
 */
function saveAlpineState(node) {
  if (!node || !window.Alpine) return;
  
  try {
    // ID'si olan tüm Alpine.js bileşenlerini bul
    const stateElements = node.querySelectorAll('[x-data][id]');
    
    stateElements.forEach(element => {
      const id = element.id;
      
      // Element Alpine.js tarafından başlatılmış mı kontrol et
      if (element.__x && element.__x.$data) {
        // Durum verilerini JSON'a dönüştür
        try {
          // Sadece temel veri tiplerini içeren özellikleri kopyala
          const state = {};
          Object.entries(element.__x.$data).forEach(([key, value]) => {
            // Fonksiyon olmayan özellikleri kopyala
            if (typeof value !== 'function' && !key.startsWith('$')) {
              state[key] = value;
            }
          });
          
          // Temizlenmiş durumu önbelleğe al
          stateCache.set(id, state);
          logger.debug(`${id} ID'li bileşenin durumu kaydedildi`);
        } catch (e) {
          logger.warn(`${id} ID'li bileşenin durumu kaydedilemedi: ${e.message}`);
        }
      }
    });
  } catch (error) {
    logger.error(`Alpine.js durum kaydetme hatası: ${error.message}`);
  }
}

/**
 * Kaydedilen Alpine.js bileşen durumlarını geri yükler
 * 
 * @param {Element} node - Alpine.js bileşenlerini içeren DOM düğümü
 */
function restoreAlpineState(node) {
  if (!node || !window.Alpine || stateCache.size === 0) return;
  
  try {
    // Önbellekte kayıtlı ID'lere sahip bileşenleri bul
    stateCache.forEach((state, id) => {
      const element = node.querySelector(`#${id}`);
      
      // Element var mı ve Alpine.js tarafından başlatılmış mı kontrol et
      if (element && element.__x && element.__x.$data) {
        // Durum verilerini Alpine.js bileşenine aktar
        Object.entries(state).forEach(([key, value]) => {
          if (key in element.__x.$data && typeof element.__x.$data[key] !== 'function') {
            element.__x.$data[key] = value;
          }
        });
        
        logger.debug(`${id} ID'li bileşenin durumu geri yüklendi`);
      }
    });
    
    // Önbelleği temizle
    stateCache.clear();
  } catch (error) {
    logger.error(`Alpine.js durum geri yükleme hatası: ${error.message}`);
  }
}

// Sayfa yüklendiğinde HTMX entegrasyonunu otomatik olarak başlat
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupHtmxIntegration);
} else {
  // Sayfa zaten yüklenmişse küçük bir gecikme ile başlat
  setTimeout(setupHtmxIntegration, 10);
}

// Global API'yi dışa aktar
export default {
  setup: setupHtmxIntegration,
  hasAlpineComponents,
  initializeAlpineComponents
};