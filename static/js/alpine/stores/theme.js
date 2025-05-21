/**
 * VivaCRM - Theme Store for Alpine.js
 * 
 * Bu modül, Alpine.js için tema yönetim store'u sağlar.
 * ThemeManager ile entegre çalışarak tema değişikliklerini Alpine.js
 * bileşenlerine aktarır.
 */

import { createLogger } from '../../core/utils.js';

// Modül için logger oluştur
const logger = createLogger('Theme-Store', {
  emoji: '🎨'
});

/**
 * ThemeManager'a erişim fonksiyonu
 * Standardize edilmiş ThemeManager'a veya geriye dönük API'lara erişir
 * 
 * @returns {Object|null} ThemeManager nesnesi veya null
 */
function getStandardThemeManager() {
  // İlk olarak VivaCRM.themeManager'ı kontrol et (tercih edilen)
  if (window.VivaCRM && window.VivaCRM.themeManager) {
    return window.VivaCRM.themeManager;
  }
  
  // Geriye dönük uyumluluk için vivaCRM.themeManager'ı da kontrol et
  if (window.vivaCRM && window.vivaCRM.themeManager) {
    return window.vivaCRM.themeManager;
  }
  
  // ThemeManager bulunamadı, konsola uyarı yaz
  logger.warn('ThemeManager bulunamadı, tema değişiklikleri doğru çalışmayabilir. Daha sonra tekrar denenecek...');
  return null;
}

/**
 * Alpine.js için tema store'u
 * ThemeManager ile entegre çalışarak tema değişikliklerini takip eder
 */
export const themeStore = {
  // Durum özellikleri
  darkMode: false,
  systemPreference: false,
  themeSource: 'system',  // 'system' veya 'manual'
  
  /**
   * Store başlatma fonksiyonu
   * ThemeManager ile bağlantı kurar ve tema bilgilerini alır
   */
  init() {
    logger.info('Theme store başlatılıyor...');
    
    // ThemeManager'a eriş
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      // ThemeManager ile entegre çalış
      this.darkMode = themeManager.currentTheme === 'dark';
      this.systemPreference = themeManager.systemPreference;
      this.themeSource = themeManager.themeSource || 'system';
      
      // ThemeManager değişikliklerini dinle
      themeManager.subscribe((theme) => {
        this.darkMode = theme === 'dark';
        logger.debug(`Tema değişikliği: ${theme}`);
      });
      
      logger.info('Theme store başlatıldı - ThemeManager ile entegre');
    } else {
      // Hata durumunda başka bir script'in ThemeManager'ı yüklemesini bekle
      logger.warn('ThemeManager bulunamadı, 1 saniye sonra tekrar deneniyor...');
      
      setTimeout(() => {
        const delayedManager = getStandardThemeManager();
        if (delayedManager) {
          this.darkMode = delayedManager.currentTheme === 'dark';
          this.systemPreference = delayedManager.systemPreference;
          this.themeSource = delayedManager.themeSource || 'system';
          
          delayedManager.subscribe((theme) => {
            this.darkMode = theme === 'dark';
            logger.debug(`Tema değişikliği (gecikmeli): ${theme}`);
          });
          
          logger.info('Theme store başlatıldı - Gecikmiş ThemeManager ile entegre');
        } else {
          logger.error('ThemeManager bulunamadı, tema değişiklikleri tam olarak çalışmayabilir.');
          
          // En azından event listener'ı kur
          document.addEventListener('vivacrm:theme-changed', (e) => {
            logger.debug('vivacrm:theme-changed olayı alındı');
            if (e.detail) {
              if (typeof e.detail.theme === 'string') {
                this.darkMode = e.detail.theme === 'dark';
              } else if (typeof e.detail.darkMode === 'boolean') {
                this.darkMode = e.detail.darkMode;
              }
            }
          });
          
          // Varsayılan değerleri ayarla
          this.darkMode = document.documentElement.classList.contains('dark') || 
                          document.documentElement.getAttribute('data-theme') === 'dark';
          this.systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
      }, 1000);
    }
  },
  
  /**
   * Temayı karanlık/açık arasında değiştirir
   */
  toggle() {
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      themeManager.toggleTheme();
      this.themeSource = 'manual';
    } else {
      logger.error('ThemeManager bulunamadı, tema değiştirilemedi.');
      
      // ThemeManager yoksa manuel olarak tema değişimi
      this.darkMode = !this.darkMode;
      this.applyThemeManually(this.darkMode ? 'dark' : 'light');
      this.themeSource = 'manual';
      
      // Tema değişikliği olayını tetikle (geriye dönük uyumluluk)
      document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', { 
        detail: { 
          theme: this.darkMode ? 'dark' : 'light',
          darkMode: this.darkMode
        }
      }));
    }
  },
  
  /**
   * Sistem tercihini kullanır
   */
  useSystemPreference() {
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      themeManager.useSystemPreference();
      this.themeSource = 'system';
    } else {
      logger.error('ThemeManager bulunamadı, sistem tercihi kullanılamadı.');
      
      // ThemeManager yoksa manuel olarak sistem tercihini uygula
      this.darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.applyThemeManually(this.darkMode ? 'dark' : 'light');
      this.themeSource = 'system';
      
      // Tema değişikliği olayını tetikle (geriye dönük uyumluluk)
      document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', { 
        detail: { 
          theme: this.darkMode ? 'dark' : 'light',
          darkMode: this.darkMode,
          source: 'system'
        }
      }));
    }
  },
  
  /**
   * Temayı manuel olarak ayarlar
   * 
   * @param {string} theme - Ayarlanacak tema ('dark' veya 'light')
   */
  applyTheme(theme) {
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      themeManager.setTheme(theme);
      this.themeSource = 'manual';
    } else {
      logger.error('ThemeManager bulunamadı, tema uygulanamadı.');
      
      // ThemeManager yoksa manuel olarak tema uygula
      this.darkMode = theme === 'dark';
      this.applyThemeManually(theme);
      this.themeSource = 'manual';
      
      // Tema değişikliği olayını tetikle (geriye dönük uyumluluk)
      document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', { 
        detail: { 
          theme: theme,
          darkMode: this.darkMode,
          source: 'manual'
        }
      }));
    }
  },
  
  /**
   * ThemeManager yoksa manuel olarak tema değişimini uygular
   * Bu fonksiyon yalnızca ThemeManager bulunamadığında kullanılır
   * 
   * @private
   * @param {string} theme - Uygulanacak tema ('dark' veya 'light')
   */
  applyThemeManually(theme) {
    logger.warn('Manuel tema değişimi uygulanıyor (ThemeManager yok)');
    
    try {
      // HTML elementine tema bilgisini ekle
      if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.classList.remove('dark');
      }
      
      // Yerel depolamaya kaydet
      localStorage.setItem('vivacrm-theme', theme);
      localStorage.setItem('vivacrm-theme-source', this.themeSource);
      
      logger.info(`Tema manuel olarak değiştirildi: ${theme}`);
    } catch (error) {
      logger.error(`Manuel tema değişimi hatası: ${error.message}`);
    }
  }
};

// Global olarak dışa aktar (geriye dönük uyumluluk için)
window.VivaCRM = window.VivaCRM || {};
window.VivaCRM.Alpine = window.VivaCRM.Alpine || {};
window.VivaCRM.Alpine.themeStore = themeStore;

// Dışa aktar
export default themeStore;