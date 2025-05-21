// HTMX Configuration and Integration
import { store } from '../store/index.js';
import { utils } from './utils.js';

// Wait for HTMX to be loaded
document.addEventListener('DOMContentLoaded', () => {
    if (!window.htmx) {
        console.error('HTMX not loaded');
        return;
    }

    // Configure HTMX
    htmx.config.defaultSwapStyle = 'innerHTML';
    htmx.config.defaultSwapDelay = 0;
    htmx.config.defaultSettleDelay = 100;
    htmx.config.timeout = 30000; // 30 seconds
    htmx.config.historyCacheSize = 10;
    htmx.config.refreshOnHistoryMiss = true;

    // Add CSRF token to all requests
    document.body.addEventListener('htmx:configRequest', (event) => {
        event.detail.headers['X-CSRFToken'] = getCsrfToken();

        // Add loading state
        const target = event.detail.target;
        if (target) {
            target.classList.add('htmx-loading');
        }
    });

    // Handle successful responses
    document.body.addEventListener('htmx:afterRequest', (event) => {
        const target = event.detail.target;
        if (target) {
            target.classList.remove('htmx-loading');
        }

        // Handle success messages
        const xhr = event.detail.xhr;
        if (xhr.status >= 200 && xhr.status < 300) {
            const message = xhr.getResponseHeader('X-Success-Message');
            if (message) {
                store.addNotification({
                    type: 'success',
                    message: message,
                    timeout: 5000
                });
            }
        }
    });

    // Handle errors
    document.body.addEventListener('htmx:responseError', (event) => {
        const xhr = event.detail.xhr;
        const target = event.detail.target;

        if (target) {
            target.classList.remove('htmx-loading');
        }

        let errorMessage = 'Bir hata oluştu';

        try {
            const response = JSON.parse(xhr.responseText);
            errorMessage = response.message || response.error || errorMessage;
        } catch (e) {
            // Not JSON response
            if (xhr.status === 403) {
                errorMessage = 'Bu işlem için yetkiniz yok';
            } else if (xhr.status === 404) {
                errorMessage = 'Sayfa bulunamadı';
            } else if (xhr.status >= 500) {
                errorMessage = 'Sunucu hatası';
            }
        }

        store.addNotification({
            type: 'error',
            message: errorMessage,
            timeout: 7000
        });
    });

    // Handle before swap for Alpine.js components
    document.body.addEventListener('htmx:beforeSwap', (event) => {
        // Destroy Alpine components in the target
        const target = event.detail.target;
        if (target && window.Alpine) {
            // Find all Alpine components and destroy them
            target.querySelectorAll('[x-data]').forEach((el) => {
                if (el._x_dataStack) {
                    // Clean up Alpine data
                    Alpine.$destroy(el);
                }
            });
        }
    });

    // Handle after settle for Alpine.js
    document.body.addEventListener('htmx:afterSettle', (event) => {
        // Initialize Alpine for new content
        const target = event.detail.target;
        if (target && window.Alpine) {
            // Initialize new Alpine components
            Alpine.initTree(target);
        }

        // Dispatch custom event for other modules
        document.dispatchEvent(
            new CustomEvent('vivacrm:content-loaded', {
                detail: { target: target }
            })
        );
    });

    // Add custom HTMX extensions
    htmx.defineExtension('loading-states', {
        onEvent: function (name, evt) {
            if (name === 'htmx:beforeRequest') {
                evt.detail.target.classList.add('loading');
            } else if (name === 'htmx:afterRequest') {
                evt.detail.target.classList.remove('loading');
            }
        }
    });

    // Progress indicator
    let progressTimeout;
    document.body.addEventListener('htmx:beforeRequest', () => {
        progressTimeout = setTimeout(() => {
            document.body.classList.add('htmx-request-pending');
        }, 300);
    });

    document.body.addEventListener('htmx:afterRequest', () => {
        clearTimeout(progressTimeout);
        document.body.classList.remove('htmx-request-pending');
    });
});

// Utility function to get CSRF token
function getCsrfToken() {
    // İlk önce meta tag'den kontrol et
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }

    // Input field'dan kontrol et
    const inputToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (inputToken) {
        return inputToken.value;
    }

    // Cookie'den kontrol et
    return utils.getCookie('csrftoken') || '';
}

// Export HTMX utilities
export const htmxUtils = {
    reload: (selector) => {
        const element = document.querySelector(selector);
        if (element) {
            htmx.trigger(element, 'reload');
        }
    },

    refresh: (selector) => {
        const element = document.querySelector(selector);
        if (element && element.hasAttribute('hx-get')) {
            htmx.ajax('GET', element.getAttribute('hx-get'), element);
        }
    },

    getCsrfToken
};

// Export for debugging
if (window.location.hostname === 'localhost') {
    window.htmxUtils = htmxUtils;
}
