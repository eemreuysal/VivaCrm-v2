/**
 * Error Boundary Component
 * Component bazlı hata yönetimi
 */
import { BaseComponent } from '../core/base-component.js';
import { i18n } from '../core/i18n.js';

export class ErrorBoundary extends BaseComponent {
    constructor(element, options = {}) {
        super();
        this.element = element;
        this.options = {
            fallback: this.defaultFallback,
            onError: null,
            retryable: true,
            ...options
        };

        this.hasError = false;
        this.error = null;
        this.init();
    }

    init() {
        // Global error handler'ı override et
        this.originalErrorHandler = window.onerror;
        this.originalUnhandledRejection = window.onunhandledrejection;

        // Component error handler
        window.onerror = (message, source, lineno, colno, error) => {
            this.handleError(error || new Error(message));
            return true; // Prevent default error handling
        };

        // Promise rejection handler
        window.onunhandledrejection = (event) => {
            this.handleError(new Error(event.reason));
            return true;
        };

        // Component unmount durumunda eski handler'ları geri yükle
        this.cleanup(() => {
            window.onerror = this.originalErrorHandler;
            window.onunhandledrejection = this.originalUnhandledRejection;
        });
    }

    handleError(error) {
        this.hasError = true;
        this.error = error;

        // Custom error handler varsa çağır
        if (this.options.onError) {
            this.options.onError(error);
        }

        // Hata logla
        console.error('Error Boundary caught:', error);

        // Fallback UI göster
        this.renderErrorUI();
    }

    renderErrorUI() {
        const fallback = this.options.fallback || this.defaultFallback;
        this.element.innerHTML = fallback(this.error, this.options.retryable);

        // Retry button event listener
        if (this.options.retryable) {
            const retryButton = this.element.querySelector('[data-retry]');
            if (retryButton) {
                this.addEventListener(retryButton, 'click', () => this.retry());
            }
        }
    }

    defaultFallback(error, retryable) {
        return `
            <div class="error-boundary-fallback p-6 bg-error/10 rounded-lg border border-error">
                <div class="flex items-start space-x-3">
                    <svg class="w-6 h-6 text-error flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-error mb-1">
                            ${i18n.t('errors.general')}
                        </h3>
                        <p class="text-sm text-base-content/70 mb-3">
                            ${error.message || i18n.t('errors.unknown')}
                        </p>
                        ${retryable ? `
                            <button data-retry class="btn btn-sm btn-error">
                                ${i18n.t('common.retry')}
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    retry() {
        this.hasError = false;
        this.error = null;

        // Sayfayı yeniden yükle veya component'i yeniden render et
        if (this.options.onRetry) {
            this.options.onRetry();
        } else {
            window.location.reload();
        }
    }

    static wrap(component, options = {}) {
        const wrapper = document.createElement('div');
        wrapper.className = 'error-boundary-wrapper';

        const errorBoundary = new ErrorBoundary(wrapper, options);

        try {
            if (typeof component === 'function') {
                component(wrapper);
            } else {
                wrapper.appendChild(component);
            }
        } catch (error) {
            errorBoundary.handleError(error);
        }

        return wrapper;
    }
}

// Alpine.js directive
if (window.Alpine) {
    Alpine.directive('error-boundary', (el, { expression }) => {
        // Güvenli bir şekilde expression'ı parse et
        let options = {};
        if (expression) {
            try {
                // JSON.parse if it's a JSON string
                if (expression.trim().startsWith('{') && expression.trim().endsWith('}')) {
                    options = JSON.parse(expression);
                } else {
                    // JSON formatında dönüştürülebilir mi dene
                    try {
                        options = JSON.parse(`{${expression}}`);
                    } catch (parseError) {
                        // En son çare - JSON olarak parse edilemez ise boş obje kullan
                        console.warn('Expression could not be safely parsed:', expression);
                        options = {};
                    }
                }
            } catch (e) {
                console.error('Error parsing expression:', e);
            }
        }
        new ErrorBoundary(el, options);
    });
}

export default ErrorBoundary;
