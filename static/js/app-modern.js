// VivaCRM - Modern App Entry Point
import Alpine from 'alpinejs';
import htmx from 'htmx.org';
import './core/config.js';
import './core/alpine-init.js';
import './core/htmx.js';
import { componentLoader } from './core/component-loader.js';
import { store } from './store/index.js';
import { utils } from './core/utils.js';
import { i18n } from './core/i18n.js';
import themeManager from './theme-manager-standardized.js';

// Make Alpine and htmx globally available
window.Alpine = Alpine;
window.htmx = htmx;

// Environment configuration
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const isDebug = document.querySelector('body')?.getAttribute('data-debug') === 'true';

// VivaCRM Application
const vivacrm = {
    version: '2.0.0',
    store,
    componentLoader,
    utils,
    i18n,
    themeManager, // Standardize edilmiş ThemeManager kullanımı
    initialized: false,

    async init() {
        if (this.initialized) return;

        try {
            // Set environment
            store.set('environment', { isDevelopment, isDebug });

            // Initialize store
            store.init();
            
            // Initialize i18n
            const locale = localStorage.getItem('vivacrm-locale') || 'tr';
            await i18n.loadTranslations(locale);

            // Alpine.js başlatma işlemi alpine-components-init.js dosyasında merkezi olarak yapılıyor
            // Alpine.start() çağrısını burada kaldırıyoruz

            // Setup global error handling
            this.setupErrorHandling();

            // Load route-specific components
            await componentLoader.loadRouteComponents(window.location.pathname);

            this.initialized = true;
            console.log(`VivaCRM v${this.version} initialized`);
        } catch (error) {
            console.error('VivaCRM initialization failed:', error);
            this.store.addNotification({
                type: 'error',
                message: 'Uygulama başlatılamadı',
                timeout: 5000
            });
        }
    },

    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            if (isDevelopment) {
                console.error('Stack:', event.error.stack);
            }
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
        });

        // HTMX error handling
        document.body.addEventListener('htmx:responseError', (event) => {
            console.error('HTMX error:', event.detail);
            this.store.addNotification({
                type: 'error',
                message: 'İstek başarısız oldu',
                timeout: 5000
            });
        });
    }
};

// Make globally available
window.vivaCRM = vivacrm;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => vivacrm.init());
} else {
    vivacrm.init();
}

// HMR support for development
if (import.meta.hot) {
    import.meta.hot.accept();
    import.meta.hot.dispose(() => {
        console.log('HMR cleanup');
        // Cleanup resources
        if (window.vivaCRM?.componentLoader) {
            window.vivaCRM.componentLoader.destroy();
        }
    });
}

// Export for module usage
export default vivacrm;
