/**
 * Theme Manager - VivaCRM için merkezi tema yönetim çözümü
 * 
 * Bu dosya, standardize edilmiş ThemeManager'a yönlendirmek içindir.
 * Projedeki eskiden yapılmış ThemeManager importları çalışmaya devam etsin diye korunmuştur.
 * Yeni geliştirmelerde direkt olarak theme-manager-standardized.js kullanılmalıdır.
 * 
 * - Alpine.js store entegrasyonu
 * - Vanilla JS desteği
 * - LocalStorage ile tema tercihi kaydetme
 * - Sistem tercihini izleme
 */

import themeManager from '../theme-manager-standardized.js';

// Eski class API desteği için wrapper ve yönlendirme
export class ThemeManager {
    constructor() {
        console.warn('Bu ThemeManager class\'ı eski kodları desteklemek için vardır. theme-manager-standardized.js kullanın.');
        
        // Singleton olduğu için, istenen her yeni ThemeManager instance'ı için
        // mevcut themeManager'ı döndürüyoruz
        return themeManager;
    }
}

// Singleton instance
export default themeManager;