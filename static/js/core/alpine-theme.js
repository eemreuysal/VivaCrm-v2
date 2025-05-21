/**
 * VivaCRM v2 - Alpine.js Tema Store Entegrasyonu
 * 
 * Bu modül, merkezi tema yönetimi sistemini Alpine.js Store API'si ile 
 * entegre eder. Alpine.js komponenti içinde:
 * 
 * - $store.theme.darkMode - Koyu tema aktif mi
 * - $store.theme.toggle() - Tema değiştirme
 * - $store.theme.useSystemPreference() - Sistem tercihini kullanma
 */

import themeManager from './theme-store.js';

/**
 * Alpine.js için tema store'u oluşturur
 * @returns {Object} Alpine.js store objesi
 */
export function createThemeStore() {
  return {
    // Temel durumlar
    darkMode: themeManager.currentTheme === 'dark',
    systemPreference: themeManager.systemPreference,
    
    /**
     * Store başlatma
     */
    init() {
      // ThemeManager değişikliklerini dinle
      themeManager.subscribe((theme) => {
        this.darkMode = theme === 'dark';
      });
    },
    
    /**
     * Tema geçişi yap (açık/koyu arası)
     */
    toggle() {
      themeManager.toggleTheme();
    },
    
    /**
     * Sistem tercihini kullan
     */
    useSystemPreference() {
      themeManager.useSystemPreference();
    },
    
    /**
     * Belirli bir temayı ayarla
     * @param {string} theme - 'dark' veya 'light'
     */
    setTheme(theme) {
      themeManager.setTheme(theme, 'user');
    }
  };
}

/**
 * Alpine.js'e tema store'unu kaydet
 */
export function registerThemeStore() {
  if (window.Alpine) {
    window.Alpine.store('theme', createThemeStore());
  }
}

/**
 * Global erişim için themeManager'ı dışa aktar
 */
export { themeManager };