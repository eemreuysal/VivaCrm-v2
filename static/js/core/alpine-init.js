/**
 * VivaCRM - Alpine.js Initialization
 * 
 * Bu dosya, Alpine.js'in tüm bileşenlerini ve store'larını merkezi olarak
 * başlatan modüldür. Modüler bir yapı sağlayarak kodu daha düzenli ve 
 * bakımı kolay hale getirir.
 */

import { createLogger, formatters, ensureNamespace } from './utils.js';
import { setupHtmxIntegration } from './htmx-alpine-bridge.js';
import * as Alpine from '../alpine/index.js';

// Logger oluştur
const logger = createLogger('Alpine-Init', {
  emoji: '🏔️'
});

/**
 * Alpine.js için gerekli bileşen ve store'ları yükler
 * 
 * @param {Object} options - Başlatma seçenekleri
 * @param {boolean} options.initializeNow - Hemen başlatma/başlatmama
 * @param {string} options.pageType - Sayfa türü ('dashboard', 'auth', vb.)
 * @returns {boolean} - Başlatma başarılıysa true, değilse false
 */
export async function initializeAlpine(options = {}) {
  // Varsayılan seçenekler
  const defaultOptions = {
    initializeNow: true,  // Hemen başlat
    pageType: detectPageType(),  // Sayfa türünü otomatik algıla
    formatters: formatters,  // Tarih, para, vb. formatlama fonksiyonları
    setupHtmx: true  // HTMX entegrasyonunu kur
  };
  
  // Kullanıcı seçenekleri ile varsayılanları birleştir
  const settings = { ...defaultOptions, ...options };
  
  // Alpine.js yüklü mü kontrol et
  if (!window.Alpine) {
    logger.error('Alpine.js yüklü değil! Lütfen önce Alpine.js scriptinin yüklenmesini sağlayın.');
    return false;
  }
  
  // Alpine.js henüz başlatılmış mı kontrol et
  const viva = ensureNamespace();
  if (viva.alpineInitialized) {
    logger.warn('Alpine.js daha önce başlatılmış. Tekrar başlatılmıyor.');
    return false;
  }
  
  logger.info('Alpine.js başlatılıyor...');
  
  try {
    // Bileşenler, store'lar ve formatları kaydet
    await Alpine.registerAll({
      formatters: settings.formatters,
      pageType: settings.pageType
    });
    
    // HTMX entegrasyonunu kur (istenirse)
    if (settings.setupHtmx) {
      setupHtmxIntegration();
    }
    
    // Alpine.js'i hemen başlat (istenirse)
    if (settings.initializeNow && typeof window.Alpine.start === 'function') {
      window.Alpine.start();
      logger.info('Alpine.js başlatıldı.');
      
      // Başarıyla başlatıldığını işaretle
      viva.alpineInitialized = true;
    }
    
    // Dışa aktarılan API'yi global namespace'e ekle (geriye dönük uyumluluk için)
    viva.Alpine = viva.Alpine || {};
    viva.Alpine.initialize = initializeAlpine;
    viva.Alpine.reinitializeNode = reinitializeAlpineNode;
    
    return true;
  } catch (error) {
    logger.error(`Alpine.js başlatma hatası: ${error.message}`);
    console.error(error);
    return false;
  }
}

/**
 * Belirli bir DOM düğümündeki Alpine.js bileşenlerini yeniden başlatır
 * 
 * @param {Element} node - Yeniden başlatılacak düğüm
 * @returns {boolean} - Başarılıysa true, değilse false
 */
export function reinitializeAlpineNode(node) {
  if (!node || !window.Alpine) {
    logger.error('Alpine.js yüklü değil veya geçerli bir node sağlanmadı!');
    return false;
  }
  
  try {
    if (typeof window.Alpine.initTree === 'function') {
      window.Alpine.initTree(node);
      logger.debug('Alpine.js düğümü yeniden başlatıldı.');
      return true;
    } else {
      logger.error('Alpine.initTree metodu bulunamadı!');
      return false;
    }
  } catch (error) {
    logger.error(`Alpine.js düğümü yeniden başlatma hatası: ${error.message}`);
    return false;
  }
}

/**
 * Şu an görüntülenen sayfanın türünü URL'e bakarak algılar
 * 
 * @returns {string|null} - Algılanan sayfa türü veya null
 */
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
  
  // Belirli bir türde olmayan sayfalar için null döndür
  return null;
}

// Sayfa tamamen yüklendiğinde çalıştır
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => initializeAlpine());
} else {
  // Sayfa zaten yüklenmişse hemen başlat
  initializeAlpine();
}

// Dışa aktar
export default {
  initialize: initializeAlpine,
  reinitializeNode: reinitializeAlpineNode,
};