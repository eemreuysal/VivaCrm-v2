/**
 * VivaCRM v2 - Merkezi Tema Yönetim Sistemi
 * 
 * Bu modül, VivaCRM uygulaması genelinde açık/koyu tema yönetimini sağlar.
 * LocalStorage'da tema tercihi saklanır ve sistem tercihi (prefers-color-scheme)
 * ile senkronize edilebilir.
 */

class ThemeManager {
  /**
   * Theme Manager sınıfını başlat
   */
  constructor() {
    // Temel durum değişkenleri
    this.currentTheme = this.loadTheme();
    this.themeSource = localStorage.getItem('vivacrm-theme-source') || 'system';
    this.systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.listeners = [];
    
    // DaisyUI tema isimleri - CSS değişkenleriyle uyumlu olmalı
    this.daisyUIThemes = {
      light: 'vivacrm',
      dark: 'vivacrmDark'
    };
    
    // Sistem tercihini izle
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    this.mediaQuery.addEventListener('change', (e) => {
      this.systemPreference = e.matches;
      if (this.themeSource === 'system') {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });

    // FOUC (Flash of Unstyled Content) önlemesi
    document.addEventListener('DOMContentLoaded', () => {
      document.documentElement.classList.remove('no-js');
    });

    // Tema değişikliklerini dinle
    document.addEventListener('vivacrm:theme-changed', (e) => {
      if (e.detail && e.detail.source !== 'themeManager') {
        if (typeof e.detail.theme === 'string') {
          if (this.currentTheme !== e.detail.theme) {
            this.setTheme(e.detail.theme);
          }
        } else if (typeof e.detail.darkMode === 'boolean') {
          const theme = e.detail.darkMode ? 'dark' : 'light';
          if (this.currentTheme !== theme) {
            this.setTheme(theme);
          }
        }
      }
    });
    
    // Başlangıç temasını uygula
    this.applyTheme(this.currentTheme);
  }

  /**
   * Temayı localStorage'dan yükle veya varsayılan değer kullan
   * @returns {string} 'dark' veya 'light' tema değeri
   */
  loadTheme() {
    const saved = localStorage.getItem('vivacrm-theme');
    const source = localStorage.getItem('vivacrm-theme-source') || 'system';
    
    if (saved) {
      return saved;
    } else if (source === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } 
    
    return 'light'; // Varsayılan değer
  }

  /**
   * Temayı değiştir
   * @param {string} theme - 'dark' veya 'light'
   * @param {string} source - 'system' veya 'user' (isteğe bağlı)
   */
  setTheme(theme, source) {
    if (theme !== 'dark' && theme !== 'light') {
      console.error('Geçersiz tema değeri:', theme);
      return;
    }
    
    // Tema kaynağını güncelle
    if (source) {
      this.themeSource = source;
      localStorage.setItem('vivacrm-theme-source', source);
    }
    
    this.currentTheme = theme;
    this.applyTheme(theme);
    localStorage.setItem('vivacrm-theme', theme);
    
    // Dinleyicileri bilgilendir
    this.notifyListeners(theme);
  }

  /**
   * Temayı değiştir (toggle)
   */
  toggleTheme() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme, 'user');
  }

  /**
   * Sistem tercihini kullan
   */
  useSystemPreference() {
    const theme = this.systemPreference ? 'dark' : 'light';
    this.setTheme(theme, 'system');
  }

  /**
   * Temayı DOM'a uygula
   * @param {string} theme - 'dark' veya 'light'
   */
  applyTheme(theme) {
    // DaisyUI tema ayarları - Critical CSS ve tema CSS dosyalarıyla eşleşmeli
    const daisyUITheme = this.daisyUIThemes[theme];
    
    // Geçiş animasyonu için sınıf ekle
    document.documentElement.classList.add('theme-transition');
    
    // Tema geçişi sırasında FOUC'u önle
    setTimeout(() => {
      // DOM'a uygula
      document.documentElement.setAttribute('data-theme', daisyUITheme);
      
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      // Geçiş animasyonu sınıfını kaldır
      setTimeout(() => {
        document.documentElement.classList.remove('theme-transition');
      }, 300); // Geçiş süresiyle eşleşmeli
    }, 10);
    
    // Custom event tetikle
    this.dispatchThemeChangedEvent(theme);
  }

  /**
   * Tema değişikliği olayını tetikle
   * @param {string} theme - 'dark' veya 'light'
   */
  dispatchThemeChangedEvent(theme) {
    document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', {
      detail: { 
        theme: theme,
        darkMode: theme === 'dark',
        source: 'themeManager'
      }
    }));
  }

  /**
   * Dinleyici ekle
   * @param {Function} callback - Tema değiştiğinde çağrılacak fonksiyon
   * @returns {Function} - Dinleyiciyi kaldırmak için kullanılabilecek fonksiyon
   */
  subscribe(callback) {
    if (typeof callback !== 'function') {
      console.error('ThemeManager.subscribe: callback must be a function');
      return () => {};
    }
    
    this.listeners.push(callback);
    
    // Anında mevcut tema bilgisini gönder
    callback(this.currentTheme);
    
    // Cleanup fonksiyonunu döndür
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }

  /**
   * Tüm dinleyicilere bildirim gönder
   * @param {string} theme - 'dark' veya 'light'
   */
  notifyListeners(theme) {
    this.listeners.forEach(callback => {
      try {
        callback(theme);
      } catch (error) {
        console.error('Tema dinleyici hatası:', error);
      }
    });
  }

  /**
   * Mevcut tema bilgilerini döndür
   * @returns {Object} - Tema bilgileri
   */
  getThemeInfo() {
    return {
      currentTheme: this.currentTheme,
      themeSource: this.themeSource,
      systemPreference: this.systemPreference,
      isDark: this.currentTheme === 'dark',
      daisyUITheme: this.daisyUIThemes[this.currentTheme]
    };
  }
}

// Singleton instance
const themeManager = new ThemeManager();

export default themeManager;