// VivaCRM - Ana Konfigürasyon

/**
 * VivaCRM global konfigürasyon nesnesi
 * @namespace
 */
const vivaCRM = {
    version: '2.0.0',
    config: {
        debug: document.querySelector('body')?.getAttribute('data-debug') === 'true',
        apiUrl: '/api/v1',
        csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value,
        htmxTimeout: 30000
    },
    modules: {},
    components: {},
    utils: {}
};

// Global nesneye ekle
window.vivaCRM = vivaCRM;

// Global error handler
window.addEventListener('error', (event) => {
    if (vivaCRM.config.debug) {
        console.error('Global Error:', event.error);
    }
});

// Named export
export { vivaCRM };

// Default export
export default vivaCRM;
