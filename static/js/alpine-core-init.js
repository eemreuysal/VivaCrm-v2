/**
 * Alpine.js Core Initialization
 * 
 * Bu dosya Alpine.js'in yalnızca bir kez ve doğru sırayla başlatılmasını sağlar.
 * Tema, formatlayıcılar ve diğer temel Alpine.js bileşenleri burada başlatılır.
 */

// Alpine.js'in başlatıldığını takip edecek global değişken
window.VivaCRM = window.VivaCRM || {};
window.VivaCRM.alpineInitialized = false;

// Hata ayıklamak için log mekanizması
function log(message, type = 'info') {
  // Debug modunda ya da hata durumunda loglama yap
  const isDebug = window.VivaCRM && window.VivaCRM.debug === true;
  const prefix = '🏔️ Alpine.js: ';
  
  if (isDebug || type === 'error') {
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
}

/**
 * Alpine.js'i başlat
 */
function initAlpine() {
  // Sayfa tamamen yüklenmeden başlatmayı engelle
  if (document.readyState !== 'complete' && document.readyState !== 'interactive') {
    log('Sayfa henüz yüklenmedi, DOMContentLoaded bekleyerek tekrar denenecek', 'warn');
    return; // DOMContentLoaded olayı tarafından tekrar çağrılacak
  }

  // Alpine.js yüklü değilse çık
  if (typeof window.Alpine === 'undefined') {
    log('Alpine.js yüklü değil! Önce Alpine.js scriptini yükleyin.', 'error');
    return;
  }

  // Zaten başlatılmışsa çık
  if (window.VivaCRM.alpineInitialized) {
    log('Alpine.js daha önce başlatılmış, tekrar başlatılmıyor.', 'warn');
    return;
  }

  log('Alpine.js başlatılıyor...');

  try {
    // Tema mağazasını başlat
    initThemeStore();
    
    // Format yardımcılarını kaydet
    initFormatHelpers();

    // Alpine.js'i başlat
    if (typeof Alpine.start === 'function') {
      // Bu noktaya kadar sorun yoksa Alpine.js başlatılabilir
      Alpine.start();
      window.VivaCRM.alpineInitialized = true;
      log('Alpine.js başarıyla başlatıldı');
    } else {
      log('Alpine.js start metodu bulunamadı', 'error');
    }

    // HTMX olaylarını dinlemek için eklentileri etkinleştir
    setupHtmxIntegration();
  } catch (error) {
    log('Alpine.js başlatma hatası: ' + error.message, 'error');
    console.error(error);
  }
}

/**
 * Tema store'unu başlat - Standardize edilmiş ThemeManager ile entegre
 */
function initThemeStore() {
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
    
    return null;
  };
  
  // ThemeManager'ı yükleme fonksiyonu
  const loadThemeManager = async () => {
    return new Promise((resolve) => {
      // Önce mevcut bir ThemeManager var mı kontrol et
      const existingManager = getStandardThemeManager();
      if (existingManager) {
        resolve(existingManager);
        return;
      }
      
      try {
        // ThemeManager script'ini dinamik olarak yükle
        const script = document.createElement('script');
        script.src = '/static/js/theme-manager-standardized.js';
        script.type = 'module';
        
        script.onload = () => {
          // Yüklendikten sonra biraz bekle ve tekrar kontrol et
          setTimeout(() => {
            const manager = getStandardThemeManager();
            resolve(manager);
          }, 300);
        };
        
        script.onerror = () => {
          console.error('ThemeManager yüklenemedi.');
          resolve(null);
        };
        
        document.head.appendChild(script);
      } catch (error) {
        console.error('ThemeManager yükleme hatası:', error);
        resolve(null);
      }
    });
  };
  
  // Daha önce tanımlanmışsa çık
  if (Alpine.store('theme')) {
    log('Theme store zaten tanımlı.', 'warn');
    return;
  }
  
  log('Theme store başlatılıyor...');
  
  try {
    // ThemeManager'ı kontrol et
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      // ThemeManager ile entegre çalışan Alpine Store
      Alpine.store('theme', {
        darkMode: themeManager.currentTheme === 'dark',
        systemPreference: themeManager.systemPreference,
        
        init() {
          // ThemeManager değişikliklerini dinle
          themeManager.subscribe((theme) => {
            this.darkMode = theme === 'dark';
          });
        },
        
        toggle() {
          themeManager.toggleTheme();
        },
        
        useSystemPreference() {
          themeManager.useSystemPreference();
        },
        
        applyTheme(theme) {
          themeManager.setTheme(theme);
        }
      });
      
      // Theme store'u başlat
      if (typeof Alpine.store('theme').init === 'function') {
        Alpine.store('theme').init();
      }
      
      log(`Theme store başlatıldı (ThemeManager ile): ${Alpine.store('theme').darkMode ? 'koyu' : 'açık'} tema`);
    } else {
      // ThemeManager yok, window.themeStore'u ayarla (fallback)
      log('ThemeManager bulunamadı, fallback theme store kullanılıyor', 'warn');
      
      // Sistem tercihini öğren
      const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches;
      
      // Tema tercihi
      const savedTheme = localStorage.getItem('vivacrm-theme');
      const isDarkMode = savedTheme 
        ? savedTheme === 'dark'
        : systemPreference;
      
      // ThemeManager yoksa window.themeStore oluştur
      window.themeStore = {
        darkMode: isDarkMode,
        systemPreference: systemPreference,
        
        toggle() {
          this.darkMode = !this.darkMode;
          localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
          localStorage.setItem('vivacrm-theme-source', 'manual');
          this.applyTheme(this.darkMode ? 'dark' : 'light');
          
          // Tema değişikliği olayını tetikle
          document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', {
            detail: { 
              theme: this.darkMode ? 'dark' : 'light', 
              darkMode: this.darkMode,
              source: 'alpineCore'
            }
          }));
        },
        
        useSystemPreference() {
          this.darkMode = this.systemPreference;
          localStorage.setItem('vivacrm-theme-source', 'system');
          localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
          this.applyTheme(this.darkMode ? 'dark' : 'light');
        },
        
        applyTheme(theme) {
          // Tema dönüşümü
          this.darkMode = theme === 'dark';
          
          // Tema bağımlı sınıfları ve öznitelikleri ayarla
          if (theme === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.setAttribute('data-theme', 'vivacrmDark');
          } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.setAttribute('data-theme', 'vivacrm');
          }
          
          // Event oluştur
          document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', {
            detail: { 
              theme: theme, 
              darkMode: theme === 'dark',
              source: 'alpineCore'
            }
          }));
        }
      };
      
      // Sayfaya ilk tema uygulaması
      if (!document.documentElement.hasAttribute('data-theme')) {
        window.themeStore.applyTheme(window.themeStore.darkMode ? 'dark' : 'light');
      }
      
      // Global store'u Alpine.js'e kaydet
      Alpine.store('theme', window.themeStore);
      
      // Sistem tercihini izle
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        // Sistem tercihi yalnızca kaynak 'system' ise kullanılır
        if (localStorage.getItem('vivacrm-theme-source') === 'system') {
          window.themeStore.systemPreference = e.matches;
          window.themeStore.darkMode = e.matches;
          window.themeStore.applyTheme(e.matches ? 'dark' : 'light');
        }
      });
      
      // ThemeManager yükleme denemesi - sonradan kullanmak için
      loadThemeManager().then(delayedManager => {
        if (delayedManager) {
          log('ThemeManager sonradan yüklendi, senkronize ediliyor...', 'warn');
          
          // Mevcut tema tercihini ThemeManager'a bildir
          const currentTheme = window.themeStore.darkMode ? 'dark' : 'light';
          const source = localStorage.getItem('vivacrm-theme-source') || 'user';
          delayedManager.setTheme(currentTheme, source);
          
          // ThemeManager değişikliklerini dinle ve Alpine store'a yansıt
          delayedManager.subscribe((theme) => {
            window.themeStore.darkMode = theme === 'dark';
            
            // Alpine store'u güncelle
            if (Alpine.store('theme')) {
              Alpine.store('theme').darkMode = theme === 'dark';
            }
          });
        }
      });
      
      log(`Theme store başlatıldı (Fallback): ${Alpine.store('theme').darkMode ? 'koyu' : 'açık'} tema`);
    }
  } catch (error) {
    log('Theme store başlatma hatası: ' + error.message, 'error');
    console.error(error);
  }
}

/**
 * Format yardımcılarını kaydet
 */
function initFormatHelpers() {
  // Format yardımcılarını global olarak tanımla
  window.formatNumber = function(number, decimals = 0) {
    if (number === null || number === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(number);
  };
  
  window.formatCurrency = function(amount) {
    if (amount === null || amount === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };
  
  window.formatDate = function(date, format = 'short') {
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
  };
  
  window.formatPercent = function(value, decimals = 1) {
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
  };

  // Format fonksiyonlarını Alpine.js magic helper olarak kaydet
  if (typeof Alpine.magic === 'function') {
    Alpine.magic('formatNumber', () => window.formatNumber);
    Alpine.magic('formatCurrency', () => window.formatCurrency);
    Alpine.magic('formatDate', () => window.formatDate);
    Alpine.magic('formatPercent', () => window.formatPercent);
  }
  
  log('Format yardımcıları başarıyla kaydedildi.');
}

/**
 * HTMX entegrasyonunu kur
 */
function setupHtmxIntegration() {
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

// Sayfa yükleme durumunu kontrol et ve uygun şekilde başlat
if (document.readyState === 'loading') {
  // Sayfa hala yükleniyor, DOMContentLoaded'ı bekle
  document.addEventListener('DOMContentLoaded', initAlpine);
  log('DOMContentLoaded bekleniyor...');
} else {
  // Sayfa zaten yüklenmiş, hemen başlat
  initAlpine();
}

// Sayfa tamamen yüklendiğinde (tüm resimler, iframe'ler vb dahil) da kontrol et
window.addEventListener('load', function() {
  if (!window.VivaCRM.alpineInitialized && window.Alpine) {
    log('Load olayı sonrası tekrar başlatma deneniyor...', 'warn');
    initAlpine();
  }
});

// Modül dışa aktarımı
// Module export yerine global olarak tanımla
window.alpineCoreInit = {
  init: initAlpine,
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