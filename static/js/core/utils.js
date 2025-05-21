/**
 * VivaCRM - Core Utilities
 * 
 * Bu dosya, tüm uygulama genelinde kullanılabilecek yardımcı fonksiyonlar içerir.
 */

/**
 * Loglama mekanizması oluşturan bir fabrika fonksiyonu.
 * Modül bazlı loglama için kullanılır.
 * 
 * @param {string} moduleName - Hangi modül için logger oluşturulacağı
 * @param {Object} options - Logger ayarları
 * @returns {Object} - Logger fonksiyonları
 */
export function createLogger(moduleName, options = {}) {
  // Default ayarlar
  const settings = {
    enabled: window.VivaCRM?.debug === true || options.forceEnabled === true,
    prefix: options.prefix || moduleName,
    emoji: options.emoji || '🔷',
    level: options.level || 'info',
    allowedLevels: options.allowedLevels || ['info', 'warn', 'error']
  };

  // Loglama seviyelerine göre gösterilecek emojiler
  const levelEmojis = {
    info: settings.emoji,
    warn: '⚠️',
    error: '🔴'
  };

  // Log fonksiyonu
  function log(message, level = 'info') {
    // Logger kapalıysa ve hata değilse loglamayı atla
    if (!settings.enabled && level !== 'error') {
      return;
    }

    // Sadece izin verilen log seviyelerini göster
    if (!settings.allowedLevels.includes(level)) {
      return;
    }

    // Prefix oluştur
    const prefix = `${levelEmojis[level] || settings.emoji} ${settings.prefix}: `;
    
    // Log tipine göre konsola yaz
    switch(level) {
      case 'error':
        console.error(prefix + message);
        break;
      case 'warn':
        console.warn(prefix + message);
        break;
      default:
        console.log(prefix + message);
    }
  }

  // Logger API'sini oluştur
  return {
    log: (message) => log(message, 'info'),
    info: (message) => log(message, 'info'),
    warn: (message) => log(message, 'warn'),
    error: (message) => log(message, 'error'),
    debug: (message) => {
      // Debug modundaysa göster
      if (settings.enabled) {
        log(message, 'info');
      }
    },
    setEnabled: (enabled) => {
      settings.enabled = enabled;
    },
    group: (title, callback) => {
      if (!settings.enabled) return callback();
      
      console.group(`${settings.emoji} ${settings.prefix}: ${title}`);
      try {
        callback();
      } finally {
        console.groupEnd();
      }
    }
  };
}

/**
 * DOM yükleme durumunu kontrol eder ve belirli bir element hazır olduğunda callback'i çağırır.
 * 
 * @param {string|Element} selector - CSS seçicisi veya DOM elementi
 * @param {Function} callback - Element hazır olduğunda çağrılacak fonksiyon
 * @param {number} maxAttempts - Maksimum deneme sayısı
 * @param {number} interval - Denemeler arası bekleme süresi (ms)
 */
export function waitForElement(selector, callback, maxAttempts = 10, interval = 100) {
  let attempts = 0;
  
  const checkExist = setInterval(() => {
    attempts++;
    
    // Selector bir string ise query yap, değilse doğrudan kullan
    const element = typeof selector === 'string' 
      ? document.querySelector(selector)
      : selector;
    
    if (element) {
      clearInterval(checkExist);
      callback(element);
    } else if (attempts >= maxAttempts) {
      clearInterval(checkExist);
      console.warn(`Element bulunamadı (${selector}), maksimum deneme sayısına ulaşıldı.`);
    }
  }, interval);
}

/**
 * Bir fonksiyonu belli bir süre boyunca çağrılmasını geciktirir (debounce).
 * Aynı fonksiyon sürekli çağrılsa bile, son çağrıdan belirli bir süre sonra
 * sadece bir kez çalıştırılır.
 * 
 * @param {Function} func - Çağrılacak fonksiyon
 * @param {number} wait - Bekleme süresi (ms)
 * @returns {Function} - Debounce edilmiş fonksiyon
 */
export function debounce(func, wait = 300) {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Bir fonksiyonu belli aralıklarla çağrılmasını sınırlar (throttle).
 * Fonksiyon ne kadar sık çağrılırsa çağrılsın, belirtilen süre içinde
 * sadece bir kez çalıştırılır.
 * 
 * @param {Function} func - Çağrılacak fonksiyon
 * @param {number} limit - Minimum çağrı aralığı (ms)
 * @returns {Function} - Throttle edilmiş fonksiyon
 */
export function throttle(func, limit = 300) {
  let inThrottle;
  
  return function throttledFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Bir değerin belirli bir türde olup olmadığını kontrol eder.
 * 
 * @param {any} value - Kontrol edilecek değer
 * @param {string} type - Beklenen tür ('string', 'number', 'boolean', 'object', 'array', 'function', 'null', 'undefined')
 * @returns {boolean} - Değer belirtilen türde ise true, değilse false
 */
export function isType(value, type) {
  switch (type) {
    case 'string':
      return typeof value === 'string';
    case 'number':
      return typeof value === 'number' && !isNaN(value);
    case 'boolean':
      return typeof value === 'boolean';
    case 'object':
      return typeof value === 'object' && value !== null && !Array.isArray(value);
    case 'array':
      return Array.isArray(value);
    case 'function':
      return typeof value === 'function';
    case 'null':
      return value === null;
    case 'undefined':
      return value === undefined;
    default:
      return false;
  }
}

/**
 * Varsayılan namespace oluşturur ve yoksa global olarak tanımlar.
 * 
 * @returns {Object} VivaCRM namespace
 */
export function ensureNamespace() {
  window.VivaCRM = window.VivaCRM || {};
  return window.VivaCRM;
}

/**
 * Format yardımcı fonksiyonları
 */
export const formatters = {
  number: function(number, decimals = 0) {
    if (number === null || number === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(number);
  },
  
  currency: function(amount, currency = 'TRY') {
    if (amount === null || amount === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  },
  
  date: function(date, format = 'short') {
    if (!date) return '';
    
    try {
      const options = {
        short: { day: '2-digit', month: '2-digit', year: 'numeric' },
        medium: { day: '2-digit', month: 'short', year: 'numeric' },
        long: { day: '2-digit', month: 'long', year: 'numeric' },
        time: { hour: '2-digit', minute: '2-digit' },
        datetime: { 
          day: '2-digit', 
          month: '2-digit', 
          year: 'numeric',
          hour: '2-digit', 
          minute: '2-digit'
        }
      };
      
      if (format === 'time') {
        return new Date(date).toLocaleTimeString('tr-TR', options.time);
      } else if (format === 'datetime') {
        return new Date(date).toLocaleString('tr-TR', options.datetime);
      }
      
      return new Date(date).toLocaleDateString('tr-TR', options[format] || options.short);
    } catch (e) {
      console.error('Tarih formatlama hatası:', e);
      return date;
    }
  },
  
  percent: function(value, decimals = 1) {
    if (value === null || value === undefined) return '';
    
    const numericValue = typeof value === 'string'
      ? parseFloat(value.replace(',', '.'))
      : value;
      
    if (isNaN(numericValue)) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      style: 'percent',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(numericValue / 100);
  }
};

// Varsayılan VivaCRM namespace oluştur
ensureNamespace();