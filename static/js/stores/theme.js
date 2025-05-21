/**
 * VivaCRM v2 - Tema Store (Eski yol)
 * 
 * Bu dosya, modern tema yönetim sistemi için yönlendirme sağlar.
 * Geriye dönük uyumluluk için korunmuştur. Yeni geliştirmelerde
 * doğrudan core/alpine-theme.js kullanılmalıdır.
 */

import { createThemeStore, themeManager } from '../core/alpine-theme.js';

/**
 * Tema yönetimi için store objesi
 */
export default {
  // Durum
  darkMode: themeManager.currentTheme === 'dark',
  systemPreference: themeManager.systemPreference,
  themeSource: themeManager.themeSource,

  /**
   * Store başlatma
   */
  init() {
    // ThemeManager'dan değişiklikleri dinle
    themeManager.subscribe((theme) => {
      this.darkMode = theme === 'dark';
      this.themeSource = themeManager.themeSource;
    });
  },

  /**
   * Tema geçişi
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
   * Temayı uygula
   * @param {string} theme - 'dark' veya 'light'
   */
  applyTheme(theme) {
    themeManager.setTheme(theme);
  }
};