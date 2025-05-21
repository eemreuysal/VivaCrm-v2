/**
 * VivaCRM v2 - Tema Yönetimi (Eski sürüm)
 * 
 * Bu dosya, standardize edilmiş tema yöneticisine yönlendirme yapar.
 * Geriye dönük uyumluluk için korunmuştur. Yeni geliştirmelerde
 * doğrudan core/theme-store.js kullanılmalıdır.
 */

import themeManager from './core/theme-store.js';

// Eski window.vivaCRM referansını da destekle
if (!window.vivaCRM) {
  window.vivaCRM = {};
}
window.vivaCRM.themeManager = themeManager;

// VivaCRM namespace altında da erişim sağla
if (!window.VivaCRM) {
  window.VivaCRM = {};
}

// Eğer halihazırda bir themeManager atanmamışsa, bu dosyayı kullan
if (!window.VivaCRM.themeManager) {
  window.VivaCRM.themeManager = themeManager;
}

export default themeManager;