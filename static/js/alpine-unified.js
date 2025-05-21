/**
 * VivaCRM - Unified Alpine.js Initialization System
 * 
 * Bu dosya, Alpine.js'in merkezi bir şekilde başlatılmasını ve bileşenlerinin
 * kaydedilmesini sağlar. Farklı kodların yarattığı çakışmaları önler.
 * 
 * - Tema yönetimi
 * - Dashboard bileşenleri
 * - Formatlamalar (currency, date, number)
 * - Genel yardımcı fonksiyonlar
 */

// Hata ayıklamak için log mekanizması
const log = (message, type = 'info') => {
  // Debug modunda ya da hata durumunda loglama yap
  const isDebug = window.VivaCRM && window.VivaCRM.debug === true;
  const prefix = '🏔️ Alpine.js: ';
  
  if (isDebug || type === 'error' || type === 'warn') {
    switch(type) {
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
};

/**
 * VivaCRM global namespace
 */
window.VivaCRM = window.VivaCRM || {};
window.VivaCRM.alpineInitialized = false;

/**
 * Format Yardımcıları
 */
const formatters = {
  number: function(number, decimals = 0) {
    if (number === null || number === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(number);
  },
  
  currency: function(amount) {
    if (amount === null || amount === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
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
        long: { day: '2-digit', month: 'long', year: 'numeric' }
      };
      
      return new Date(date).toLocaleDateString('tr-TR', options[format] || options.short);
    } catch (e) {
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

/**
 * Global olarak formatters'ı dışa aktar
 */
window.formatNumber = formatters.number;
window.formatCurrency = formatters.currency;
window.formatDate = formatters.date;
window.formatPercent = formatters.percent;

/**
 * Tema Yönetimi - Standardize edilmiş ThemeManager ile entegre
 * Merkezi ThemeManager için bir Alpine.js store arayüzü sağlar
 */
// ThemeManager'a erişim fonksiyonu
const getStandardThemeManager = () => {
  // İlk olarak VivaCRM.themeManager'ı kontrol et (tercih edilen)
  if (window.VivaCRM && window.VivaCRM.themeManager) {
    return window.VivaCRM.themeManager;
  }
  
  // Geriye dönük uyumluluk için vivaCRM.themeManager'ı da kontrol et
  if (window.vivaCRM && window.vivaCRM.themeManager) {
    return window.vivaCRM.themeManager;
  }
  
  // ThemeManager bulunamadı, konsola uyarı yaz
  console.warn('ThemeManager bulunamadı, tema değişiklikleri doğru çalışmayabilir.');
  return null;
};

// Alpine.js theme store
const themeStore = {
  darkMode: false,
  systemPreference: false,
  
  init() {
    // ThemeManager'a eriş
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      // ThemeManager ile entegre çalış
      this.darkMode = themeManager.currentTheme === 'dark';
      this.systemPreference = themeManager.systemPreference;
      
      // ThemeManager değişikliklerini dinle
      themeManager.subscribe((theme) => {
        this.darkMode = theme === 'dark';
      });
      
      log('Theme store başlatıldı - ThemeManager ile entegre');
    } else {
      // Hata durumunda başka bir script'in ThemeManager'ı yüklemesini bekle
      log('ThemeManager bulunamadı, 1 saniye sonra tekrar deneniyor...', 'warn');
      
      setTimeout(() => {
        const delayedManager = getStandardThemeManager();
        if (delayedManager) {
          this.darkMode = delayedManager.currentTheme === 'dark';
          this.systemPreference = delayedManager.systemPreference;
          
          delayedManager.subscribe((theme) => {
            this.darkMode = theme === 'dark';
          });
          
          log('Theme store başlatıldı - Gecikmiş ThemeManager ile entegre');
        } else {
          log('ThemeManager bulunamadı, tema değişiklikleri tam olarak çalışmayabilir.', 'error');
          
          // En azından event listener'ı kur
          document.addEventListener('vivacrm:theme-changed', (e) => {
            if (e.detail) {
              if (typeof e.detail.theme === 'string') {
                this.darkMode = e.detail.theme === 'dark';
              } else if (typeof e.detail.darkMode === 'boolean') {
                this.darkMode = e.detail.darkMode;
              }
            }
          });
        }
      }, 1000);
    }
  },
  
  toggle() {
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      themeManager.toggleTheme();
    } else {
      log('ThemeManager bulunamadı, tema değiştirilemedi.', 'error');
    }
  },
  
  useSystemPreference() {
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      themeManager.useSystemPreference();
    } else {
      log('ThemeManager bulunamadı, sistem tercihi kullanılamadı.', 'error');
    }
  },
  
  applyTheme(theme) {
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      themeManager.setTheme(theme);
    } else {
      log('ThemeManager bulunamadı, tema uygulanamadı.', 'error');
    }
  }
};

/**
 * Dashboard Bileşenleri - Yalnızca dashboard sayfasında kullanılır
 */
function importDashboardComponents() {
  // Komponent global tanımlaması - dummy fonksiyonlar ile
  window.dashboardComponent = window.dashboardComponent || function() {
    return {
      loading: false,
      currentPeriod: 'month',
      customStartDate: null,
      customEndDate: null,
      charts: {},
      
      initialize() {
        log('Dashboard component dummy initialize çağrıldı. Gerçek dashboard-components.js yüklendikten sonra tekrar deneyin.', 'warn');
      },
      
      initializeCharts() {
        log('Dashboard charts dummy initialize çağrıldı. Gerçek dashboard-components.js yüklendikten sonra tekrar deneyin.', 'warn');
      }
    };
  };
  
  window.dateFilterComponent = window.dateFilterComponent || function() {
    return {
      showDatePicker: false,
      startDate: null,
      endDate: null,
      
      init() {
        log('Date filter component dummy init çağrıldı. Gerçek dashboard-components.js yüklendikten sonra tekrar deneyin.', 'warn');
      }
    };
  };
  
  // Asenkron olarak dashboard bileşenlerini yükle
  const dashboardScriptUrl = '/static/js/components/dashboard-components.js';
  
  if (document.querySelector('script[src*="dashboard-components.js"]')) {
    log('Dashboard components script zaten yükleniyor veya yüklenmiş.');
    return;
  }
  
  const script = document.createElement('script');
  script.src = dashboardScriptUrl;
  script.type = 'module';
  script.onload = () => {
    log('Dashboard components script yüklendi. Bileşenler kaydediliyor...');
    
    // Script type=module olduğu için doğrudan erişilemez, 
    // dashboard-init.js tarafından kaydedilmesi gerekiyor
    // Bu dosya dashboard-init.js'i tetikler
  };
  script.onerror = (err) => {
    log('Dashboard components script yüklenemedi: ' + err, 'error');
  };
  document.head.appendChild(script);
  
  // Dashboard init script'ini ekle
  const initScriptUrl = '/static/js/dashboard-init.js';
  
  if (document.querySelector('script[src*="dashboard-init.js"]')) {
    log('Dashboard init script zaten yükleniyor veya yüklenmiş.');
    return;
  }
  
  const initScript = document.createElement('script');
  initScript.src = initScriptUrl;
  initScript.defer = true;
  document.head.appendChild(initScript);
}

/**
 * HTMX Entegrasyonu
 */
function setupHtmxIntegration() {
  // Sayfa yükleme durumunu kontrol et
  if (!document.body) {
    log('HTMX entegrasyonu için document.body henüz hazır değil.', 'warn');
    return;
  }
  
  // HTMX içerik güncellemelerinden sonra Alpine bileşenlerini güncelle
  document.body.addEventListener('htmx:afterSwap', function(event) {
    // Hedef elementi al
    const swappedNode = event.detail.target;
    
    // Alpine bileşenlerini içeriyor mu kontrol et
    if (swappedNode.querySelector('[x-data]') || swappedNode.hasAttribute('x-data')) {
      log('HTMX sonrası Alpine.js bileşenleri tespit edildi, yeniden başlatılıyor');
      
      // Güvenlik için küçük bir gecikme ekle
      setTimeout(() => {
        // Alpine.js bileşenlerini hedef node'da yeniden başlat
        if (typeof Alpine.initTree === 'function') {
          try {
            Alpine.initTree(swappedNode);
            log('HTMX sonrası Alpine.js bileşenleri başarıyla yeniden başlatıldı');
          } catch (error) {
            log('HTMX sonrası Alpine.js başlatma hatası: ' + error.message, 'error');
          }
        } else {
          log('Alpine.initTree metodu bulunamadı, bileşenler başlatılamadı', 'error');
        }
      }, 10); // Kısa bir gecikme ekle
    }
  });
  
  // HTMX ile sayfa yüklendiğinde de Alpine'ı kontrol et
  document.body.addEventListener('htmx:load', function(event) {
    const loadedNode = event.detail.elt;
    
    // Alpine bileşenlerini içeriyor mu kontrol et
    if (loadedNode.querySelector('[x-data]') || loadedNode.hasAttribute('x-data')) {
      log('HTMX load sonrası Alpine.js bileşenleri tespit edildi');
      
      // Alpine.js bileşenlerini hedef node'da başlat
      if (typeof Alpine.initTree === 'function') {
        try {
          Alpine.initTree(loadedNode);
          log('HTMX load sonrası Alpine.js bileşenleri başarıyla başlatıldı');
        } catch (error) {
          log('HTMX load sonrası Alpine.js başlatma hatası: ' + error.message, 'error');
        }
      }
    }
  });
  
  log('HTMX entegrasyonu kuruldu');
}

/**
 * Alpine.js'i başlat
 */
function initializeAlpine() {
  // Alpine.js zaten başlatılmışsa çık
  if (window.VivaCRM.alpineInitialized) {
    log('Alpine.js daha önce başlatılmış. Tekrar başlatılmıyor.', 'warn');
    return;
  }
  
  // Alpine.js yüklenmemişse çık
  if (typeof window.Alpine === 'undefined') {
    log('Alpine.js yüklü değil! Önce Alpine.js kütüphanesini ekleyin.', 'error');
    return;
  }
  
  log('Alpine.js başlatılıyor...');
  
  try {
    // Stores ve Global Helper'ları kaydet
    Alpine.store('theme', themeStore);
    
    // Format magic helper'ları kaydet
    if (typeof Alpine.magic === 'function') {
      Alpine.magic('formatNumber', () => formatters.number);
      Alpine.magic('formatCurrency', () => formatters.currency);
      Alpine.magic('formatDate', () => formatters.date);
      Alpine.magic('formatPercent', () => formatters.percent);
    }
    
    // Tema store'unu başlat
    themeStore.init();
    
    // Dashboard sayfasında mıyız kontrol et
    if (window.location.pathname.includes('/dashboard')) {
      importDashboardComponents();
    }
    
    // HTMX entegrasyonunu kur
    setupHtmxIntegration();
    
    // Alpine.js'i başlat
    if (typeof Alpine.start === 'function') {
      Alpine.start();
      window.VivaCRM.alpineInitialized = true;
      log('Alpine.js başarıyla başlatıldı');
    } else {
      log('Alpine.start metodu bulunamadı!', 'error');
    }
  } catch (error) {
    log('Alpine.js başlatma hatası: ' + error.message, 'error');
    console.error(error);
  }
}

// Sayfa yükleme durumunu kontrol et ve uygun şekilde başlat
if (document.readyState === 'loading') {
  // Sayfa hala yükleniyor, DOMContentLoaded'ı bekle
  document.addEventListener('DOMContentLoaded', initializeAlpine);
  log('DOMContentLoaded bekleniyor...');
} else {
  // Sayfa zaten yüklenmiş, hemen başlat
  initializeAlpine();
}

// Sayfa tamamen yüklendiğinde de kontrol et
window.addEventListener('load', function() {
  if (!window.VivaCRM.alpineInitialized && window.Alpine) {
    log('Load olayı sonrası tekrar başlatma deneniyor...', 'warn');
    initializeAlpine();
  }
});

// Global olarak erişilebilir temiz API
window.VivaCRM.Alpine = {
  initialize: initializeAlpine,
  reinitializeNode: function(node) {
    if (window.Alpine && typeof Alpine.initTree === 'function') {
      try {
        Alpine.initTree(node);
        return true;
      } catch (error) {
        log('Node yeniden başlatma hatası: ' + error.message, 'error');
        return false;
      }
    }
    return false;
  }
};

// Global formatters
window.formatters = formatters;