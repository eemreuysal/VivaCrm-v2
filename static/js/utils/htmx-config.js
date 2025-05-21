/**
 * HTMX Config
 *
 * HTMX için yapılandırma ve özelleştirmeler
 * @module utils/htmx-config
 */

// HTMX global ayarları
document.addEventListener('DOMContentLoaded', () => {
    if (!window.htmx) {
        console.warn('HTMX not found, skipping configuration');
        return;
    }

    // CSRF token'ı ayarla
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
    // HTMX için CSRF token'ı ayarla
        htmx.config.headers = {
            ...htmx.config.headers,
            'X-CSRFToken': csrfToken
        };

        // Tüm istekler için CSRF token'ı header'a ekle
        document.body.setAttribute('hx-headers', JSON.stringify({
            'X-CSRFToken': csrfToken
        }));
    }

    // HTMX olay işleyicileri
    document.body.addEventListener('htmx:configRequest', (event) => {
    // İstek yapılandırması
        event.detail.headers = {
            ...event.detail.headers,
            'X-Requested-With': 'XMLHttpRequest'
        };
    });

    document.body.addEventListener('htmx:beforeSwap', (_event) => {
    // Swap öncesi işlemler
    });

    document.body.addEventListener('htmx:afterSwap', (_event) => {
    // Swap sonrası işlemler

        // Alpine.js komponentlerini güncelle - bu artık alpine-init.js'de daha kapsamlı şekilde yapılıyor
        // Burada sadece özel gereksinimler olursa işlemler eklenir
        if (window.Alpine && window.VivaCRM && typeof window.VivaCRM.alpineInitialized !== 'undefined') {
            // Loglama debug modunda açık
            if (window.VivaCRM && window.VivaCRM.debug === true) {
                console.log('htmx:afterSwap - Alpine işlemleri alpine-init.js tarafından yönetiliyor');
            }
        }
    });

    document.body.addEventListener('htmx:responseError', (event) => {
    // Hata durumunda bildirim göster
    // Notification store'u kontrol et ve kullan
        if (window.Alpine?.store('notification')) {
            window.Alpine.store('notification').error(
                `İstek sırasında bir hata oluştu: ${event.detail.error}`,
                8000
            );
        }
    });

    // Debug modunda log göster
    if (window.VivaCRM && window.VivaCRM.debug === true) {
        console.info('HTMX configuration applied successfully');
    }
});
