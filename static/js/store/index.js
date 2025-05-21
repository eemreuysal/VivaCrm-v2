/**
 * VivaCRM Store - Refactored with Single Responsibility Principle
 */
import { StateManager } from './state-manager.js';
import { CacheManager } from './cache-manager.js';
import { NotificationManager } from './notification-manager.js';
import themeManager from '../theme-manager-standardized.js';

class VivaCRMStore {
    constructor() {
        this.state = new StateManager();
        this.cache = new CacheManager();
        this.notifications = new NotificationManager();
        this.theme = themeManager; // Standardize edilmiş ThemeManager
        this.initialized = false;
    }

    /**
     * Store'u başlat
     */
    init() {
        if (this.initialized) return;

        // CSRF token'ı yükle
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            this.state.set('csrfToken', csrfToken);
        }

        // User bilgilerini yükle
        const userData = document.querySelector('body')?.dataset?.user;
        if (userData) {
            this.state.set('user', JSON.parse(userData));
        }

        // Standardize edilmiş ThemeManager'ı global olarak erişilebilir yap
        if (!window.VivaCRM) {
            window.VivaCRM = {};
        }
        window.VivaCRM.themeManager = this.theme;

        // Eski kodlar için geriye uyumluluk
        if (!window.vivaCRM) {
            window.vivaCRM = {};
        }
        window.vivaCRM.themeManager = this.theme;

        this.initialized = true;
        console.log('VivaCRM store initialized with standardized ThemeManager');
    }

    // Kısayol metodları (backward compatibility için)
    set(key, value) {
        if (key === 'theme') {
            return this.theme.setTheme(value);
        }
        return this.state.set(key, value);
    }

    get(key) {
        if (key === 'theme') {
            return this.theme.currentTheme;
        }
        return this.state.get(key);
    }

    addNotification(notification) {
        return this.notifications.add(notification);
    }

    removeNotification(id) {
        return this.notifications.remove(id);
    }

    setTheme(theme) {
        return this.theme.setTheme(theme);
    }

    getTheme() {
        return this.theme.currentTheme;
    }

    // Cache metodları
    setCache(key, value, ttl) {
        return this.cache.set(key, value, ttl);
    }

    getCache(key) {
        return this.cache.get(key);
    }

    clearCache() {
        return this.cache.clear();
    }
}

// Singleton instance
export const store = new VivaCRMStore();

// Alpine.js store olarak ta kullanılabilir
if (window.Alpine) {
    window.Alpine.store('viva', store);
}

// Global olarak erişim için standardize edilmiş değişken adı (büyük harfli)
if (!window.VivaCRM) {
    window.VivaCRM = {};
}
window.VivaCRM.store = store;

// Geriye dönük uyumluluk için (küçük harfli)
if (!window.vivaCRM) {
    window.vivaCRM = {};
}
window.vivaCRM.store = store;

// Store'u başlat
document.addEventListener('DOMContentLoaded', () => {
    store.init();
});

export default store;