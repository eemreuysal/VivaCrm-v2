// VivaCRM - Lazy Loading Image Module

/**
 * Lazy loading image implementasyonu
 * IntersectionObserver kullanarak performans optimizasyonu
 * @class LazyImage
 */
export class LazyImage {
    /**
     * @param {Object} options - Konfigürasyon seçenekleri
     * @param {string} [options.selector='[data-lazy-src]'] - Lazy load edilecek elementlerin selector'u
     * @param {number} [options.threshold=0.1] - Intersection threshold
     * @param {string} [options.rootMargin='50px'] - Root margin
     * @param {string} [options.loadingClass='loading'] - Yüklenirken eklenecek class
     * @param {string} [options.loadedClass='loaded'] - Yüklendikten sonra eklenecek class
     * @param {string} [options.errorClass='error'] - Hata durumunda eklenecek class
     */
    constructor(options = {}) {
        this.selector = options.selector || '[data-lazy-src]';
        this.threshold = options.threshold || 0.1;
        this.rootMargin = options.rootMargin || '50px';
        this.loadingClass = options.loadingClass || 'loading';
        this.loadedClass = options.loadedClass || 'loaded';
        this.errorClass = options.errorClass || 'error';

        this.observer = null;
        this.init();
    }

    /**
     * Observer'ı başlat
     */
    init() {
        // IntersectionObserver desteği kontrolü
        if (!('IntersectionObserver' in window)) {
            // Fallback: tüm resimleri hemen yükle
            this.loadAllImages();
            return;
        }

        // Observer oluştur
        this.observer = new IntersectionObserver(
            this.handleIntersection.bind(this),
            {
                threshold: this.threshold,
                rootMargin: this.rootMargin
            }
        );

        // Mevcut elementleri observe et
        this.observeImages();

        // DOM değişikliklerini dinle
        this.setupMutationObserver();
    }

    /**
     * Intersection handler
     * @param {IntersectionObserverEntry[]} entries - Observer entries
     */
    handleIntersection(entries) {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                this.loadImage(entry.target);
                this.observer.unobserve(entry.target);
            }
        });
    }

    /**
     * Resmi yükle
     * @param {HTMLElement} element - Yüklenecek element
     */
    loadImage(element) {
        const src = element.dataset.lazySrc;
        const srcset = element.dataset.lazySrcset;

        if (!src) return;

        // Loading state
        element.classList.add(this.loadingClass);

        // img veya div background-image kontrolü
        if (element.tagName === 'IMG') {
            // Geçici image objesi oluştur
            const tempImg = new Image();

            tempImg.onload = () => {
                element.src = src;
                if (srcset) {
                    element.srcset = srcset;
                }
                element.classList.remove(this.loadingClass);
                element.classList.add(this.loadedClass);
                this.onImageLoaded(element);
            };

            tempImg.onerror = () => {
                element.classList.remove(this.loadingClass);
                element.classList.add(this.errorClass);
                this.onImageError(element);
            };

            // Yüklemeyi başlat
            if (srcset) {
                tempImg.srcset = srcset;
            }
            tempImg.src = src;
        } else {
            // Background image için
            element.style.backgroundImage = `url(${src})`;
            element.classList.remove(this.loadingClass);
            element.classList.add(this.loadedClass);
        }

        // Data attribute'ları temizle
        delete element.dataset.lazySrc;
        delete element.dataset.lazySrcset;
    }

    /**
     * Tüm resimleri observe et
     */
    observeImages() {
        const images = document.querySelectorAll(this.selector);
        images.forEach((img) => this.observer.observe(img));
    }

    /**
     * DOM değişikliklerini dinle
     */
    setupMutationObserver() {
        const mutationObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        // Eklenen element lazy load attribute'una sahipse
                        if (node.matches && node.matches(this.selector)) {
                            this.observer.observe(node);
                        }

                        // Alt elementleri kontrol et
                        const lazyElements = node.querySelectorAll(this.selector);
                        lazyElements.forEach((el) => this.observer.observe(el));
                    }
                });
            });
        });

        mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Fallback: Tüm resimleri hemen yükle
     */
    loadAllImages() {
        const images = document.querySelectorAll(this.selector);
        images.forEach((img) => this.loadImage(img));
    }

    /**
     * Resim yüklendiğinde çağrılır
     * @param {HTMLElement} element - Yüklenen element
     */
    onImageLoaded(element) {
        // Custom event dispatch
        element.dispatchEvent(new CustomEvent('lazyloaded', {
            detail: { src: element.src }
        }));
    }

    /**
     * Resim yüklenemediğinde çağrılır
     * @param {HTMLElement} element - Hata veren element
     */
    onImageError(element) {
        // Custom event dispatch
        element.dispatchEvent(new CustomEvent('lazyerror', {
            detail: { src: element.dataset.lazySrc }
        }));
    }

    /**
     * Observer'ı temizle
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

/**
 * Alpine.js directive for lazy loading
 */
if (window.Alpine) {
    Alpine.directive('lazy', (el, { expression }) => {
        // Set data attribute
        el.dataset.lazySrc = expression || el.src;

        // Initialize lazy loading
        if (!window.lazyImageInstance) {
            window.lazyImageInstance = new LazyImage();
        }

        // Observe element
        window.lazyImageInstance.observer.observe(el);
    });
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    new LazyImage();
});

export default LazyImage;
