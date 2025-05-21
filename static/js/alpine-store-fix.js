/**
 * Alpine.js Store Fix
 * 
 * VivaCRM için Alpine.js store yönetimini düzeltir.
 * ThemeManager ile entegre çalışır.
 */

// Not: theme-manager.js modülünü doğrudan import edemiyoruz çünkü bu dosya
// script etiketiyle dahil ediliyor. Bunun yerine global ThemeManager'ı kullanıyoruz.

document.addEventListener('DOMContentLoaded', function() {
  // Alpine.js yüklü mü kontrol et
  if (window.Alpine) {
    console.log('Alpine.js detected, initializing store fix');
    
    // ThemeManager'ı tanımla veya global değişkenden al
    const getThemeManager = () => {
      // Global ThemeManager varsa kullan
      if (window.vivaCRM && window.vivaCRM.themeManager) {
        return window.vivaCRM.themeManager;
      }
      
      console.warn('ThemeManager not found, will initialize when available');
      return null;
    };
    
    // ThemeManager'ı bekleyecek fonksiyon
    const initWithThemeManager = (callback) => {
      const interval = setInterval(() => {
        const manager = getThemeManager();
        if (manager) {
          clearInterval(interval);
          callback(manager);
        }
      }, 100);
      
      // En fazla 3 saniye bekle
      setTimeout(() => {
        clearInterval(interval);
        console.error('ThemeManager not available after timeout');
      }, 3000);
    };
    
    // Alpine.js theme store tanımını dinamik olarak oluştur
    initWithThemeManager(themeManager => {
      // Mevcut tema bilgisini ThemeManager'dan al
      const themeInfo = themeManager.getThemeInfo();
      
      // Alpine.js theme store'u tanımla
      Alpine.store('theme', {
        darkMode: themeInfo.isDark,
        systemPreference: themeInfo.systemPreference,
        themeSource: themeInfo.themeSource,
        
        init() {
          // ThemeManager değişikliklerini dinle
          themeManager.subscribe((theme) => {
            this.darkMode = theme === 'dark';
            this.themeSource = themeManager.themeSource;
          });
          
          console.log('Theme store initialized with ThemeManager integration');
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
      
      // Theme store'u başlat (eğer otomatik başlatılmadıysa)
      if (Alpine.store('theme') && typeof Alpine.store('theme').init === 'function') {
        Alpine.store('theme').init();
      }
    });
  } else {
    console.error('Alpine.js is not loaded');
  }
});