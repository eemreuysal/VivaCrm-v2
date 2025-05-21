/**
 * VivaCRM - Alpine.js Bileşen Kaydı
 * 
 * Bu dosya, tüm Alpine.js bileşenlerini merkezi olarak yönetir ve
 * gerekli olduğunda kayıt eder. Bu sayede bileşenlerin modüler bir yapıda
 * tutulması ve gerektiğinde import edilmesi sağlanır.
 */

import { createLogger } from '../core/utils.js';
import { themeStore } from './stores/theme.js';

// Dashboard bileşenleri
import dashboardComponent from './components/dashboard.js';
import dateFilterComponent from './components/date-filter.js';
import ordersTableComponent from './components/orders-table.js';

// Diğer bileşenler gerektiğinde buraya eklenebilir
// import cardComponent from './components/card.js';
// import modalComponent from './components/modal.js';

// Modül için logger oluştur
const logger = createLogger('Alpine-Registry', {
  emoji: '🏔️'
});

/**
 * Alpine.js'in hazır olup olmadığını kontrol eder
 * @returns {boolean} Alpine.js hazırsa true, değilse false
 */
export function isAlpineReady() {
  return typeof window.Alpine !== 'undefined';
}

/**
 * Tüm Alpine.js bileşenlerini kaydeder
 * @returns {boolean} Kayıt başarılıysa true, değilse false
 */
export function registerComponents() {
  if (!isAlpineReady()) {
    logger.error('Alpine.js yüklü değil! Bileşenler kaydedilemedi.');
    return false;
  }

  try {
    logger.info('Alpine.js bileşenleri kaydediliyor...');

    // Alpine.data() metoduyla bileşenleri kaydet
    if (typeof Alpine.data === 'function') {
      // Dashboard bileşenlerini kaydet
      Alpine.data('dashboardComponent', dashboardComponent);
      Alpine.data('dateFilterComponent', dateFilterComponent);
      Alpine.data('ordersTableApp', ordersTableComponent);

      // Gerektiğinde diğer bileşenler burada kaydedilecek

      logger.info('Alpine.js bileşenleri başarıyla kaydedildi');
      return true;
    } else {
      logger.error('Alpine.data() metodu bulunamadı! Alpine.js sürümünüzü kontrol edin.');
      return false;
    }
  } catch (error) {
    logger.error(`Bileşen kaydı sırasında hata: ${error.message}`);
    console.error(error);
    return false;
  }
}

/**
 * Alpine.js store'larını kaydeder
 * @returns {boolean} Kayıt başarılıysa true, değilse false
 */
export function registerStores() {
  if (!isAlpineReady()) {
    logger.error('Alpine.js yüklü değil! Store\'lar kaydedilemedi.');
    return false;
  }

  try {
    logger.info('Alpine.js store\'ları kaydediliyor...');

    // Alpine.store() metoduyla store'ları kaydet
    if (typeof Alpine.store === 'function') {
      // Tema store'unu kaydet
      Alpine.store('theme', themeStore);

      // Diğer store'lar gerektiğinde ileride eklenebilir

      logger.info('Alpine.js store\'ları başarıyla kaydedildi');
      return true;
    } else {
      logger.error('Alpine.store() metodu bulunamadı! Alpine.js sürümünüzü kontrol edin.');
      return false;
    }
  } catch (error) {
    logger.error(`Store kaydı sırasında hata: ${error.message}`);
    console.error(error);
    return false;
  }
}

/**
 * Format yardımcılarını Alpine.js'e kaydeder
 * @param {Object} formatters - Format yardımcıları
 * @returns {boolean} Kayıt başarılıysa true, değilse false
 */
export function registerFormatHelpers(formatters) {
  if (!isAlpineReady()) {
    logger.error('Alpine.js yüklü değil! Format yardımcıları kaydedilemedi.');
    return false;
  }

  if (!formatters) {
    logger.error('Format yardımcıları tanımlanmamış!');
    return false;
  }

  try {
    logger.info('Alpine.js format yardımcıları kaydediliyor...');

    // Alpine.magic() metoduyla magic helper'ları kaydet
    if (typeof Alpine.magic === 'function') {
      // Formatters'ları kaydet
      if (formatters.number) Alpine.magic('formatNumber', () => formatters.number);
      if (formatters.currency) Alpine.magic('formatCurrency', () => formatters.currency);
      if (formatters.date) Alpine.magic('formatDate', () => formatters.date);
      if (formatters.percent) Alpine.magic('formatPercent', () => formatters.percent);

      logger.info('Alpine.js format yardımcıları başarıyla kaydedildi');
      return true;
    } else {
      logger.error('Alpine.magic() metodu bulunamadı! Alpine.js sürümünüzü kontrol edin.');
      return false;
    }
  } catch (error) {
    logger.error(`Format yardımcıları kaydı sırasında hata: ${error.message}`);
    console.error(error);
    return false;
  }
}

/**
 * Sayfa türüne göre özel bileşenleri yükler
 * @param {string} pageType - Sayfa türü ('dashboard', 'auth', vb.)
 * @returns {Promise<boolean>} - Yükleme başarılıysa true, değilse false
 */
export async function loadPageSpecificComponents(pageType) {
  if (!isAlpineReady()) {
    logger.error('Alpine.js yüklü değil! Sayfa bileşenleri yüklenemedi.');
    return false;
  }

  if (!pageType) {
    logger.warn('Sayfa türü belirtilmedi, özel bileşenler yüklenmeyecek.');
    return false;
  }

  logger.info(`${pageType} sayfası için özel bileşenler yükleniyor...`);

  try {
    // Sayfa türüne göre bileşenleri kaydet
    switch (pageType.toLowerCase()) {
      case 'dashboard':
        // Dashboard bileşenlerini modülden kaydet
        if (typeof Alpine.data === 'function') {
          // dashboardComponent, dateFilterComponent ve ordersTableComponent
          // zaten import edildi ve kaydedildi
          logger.info('Dashboard bileşenleri başarıyla kaydedildi');
          return true;
        }
        break;
        
      // Diğer sayfa türleri gerektiğinde burada eklenecek
        
      default:
        logger.warn(`'${pageType}' sayfa türü için tanımlı bileşen grubu yok.`);
        return false;
    }
  } catch (error) {
    logger.error(`Sayfa bileşenleri yüklenirken hata: ${error.message}`);
    console.error(error);
    return false;
  }

  return false;
}

/**
 * Tüm Alpine.js kaydını (bileşenler, store'lar, format yardımcıları) yapar
 * @param {Object} options - Kayıt seçenekleri
 * @returns {Promise<boolean>} - Kayıt başarılıysa true, değilse false
 */
export async function registerAll(options = {}) {
  const { formatters, pageType } = options;

  let success = true;

  // Temel bileşenleri kaydet
  if (!registerComponents()) {
    success = false;
  }

  // Store'ları kaydet
  if (!registerStores()) {
    success = false;
  }

  // Format yardımcılarını kaydet (eğer sağlanmışsa)
  if (formatters && !registerFormatHelpers(formatters)) {
    success = false;
  }

  // Sayfa türüne özel bileşenleri yükle (eğer belirtilmişse)
  if (pageType) {
    const pageSpecificSuccess = await loadPageSpecificComponents(pageType);
    if (!pageSpecificSuccess) {
      success = false;
    }
  }

  // Global nesnelere ekle (geriye dönük uyumluluk için)
  window.VivaCRM = window.VivaCRM || {};
  window.VivaCRM.Alpine = window.VivaCRM.Alpine || {};
  window.VivaCRM.Alpine.registry = {
    registerComponents,
    registerStores,
    registerFormatHelpers,
    loadPageSpecificComponents,
    registerAll
  };

  return success;
}

// Geriye dönük uyumluluk için global değişkenleri güncelle
window.dashboardComponent = dashboardComponent;
window.dateFilterComponent = dateFilterComponent;
window.ordersTableApp = ordersTableComponent;