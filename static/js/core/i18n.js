/**
 * i18n (Internationalization) Manager
 * Çoklu dil desteği için altyapı
 */
export class I18n {
    constructor() {
        this.currentLocale = 'tr';
        this.translations = {};
        this.fallbackLocale = 'tr';
    }

    /**
     * Çevirileri yükle
     */
    async loadTranslations(locale = this.currentLocale) {
        try {
            const response = await fetch(`/static/locales/${locale}.json`);
            if (!response.ok) {
                throw new Error(`Translation file not found for locale: ${locale}`);
            }

            this.translations[locale] = await response.json();
            this.currentLocale = locale;

            // LocalStorage'a kaydet
            localStorage.setItem('vivacrm-locale', locale);

            return true;
        } catch (error) {
            console.error(`Failed to load translations for ${locale}:`, error);

            // Fallback locale'e dön
            if (locale !== this.fallbackLocale) {
                return this.loadTranslations(this.fallbackLocale);
            }

            return false;
        }
    }

    /**
     * Çeviri metni getir
     */
    t(key, params = {}) {
        const keys = key.split('.');
        let translation = this.translations[this.currentLocale];

        // Nested key desteği
        for (const k of keys) {
            if (translation && translation[k]) {
                translation = translation[k];
            } else {
                // Fallback locale'den bak
                translation = this.getFallbackTranslation(keys);
                break;
            }
        }

        // Bulunamazsa key'i döndür
        if (typeof translation !== 'string') {
            console.warn(`Translation not found for key: ${key}`);
            return key;
        }

        // Parametre değiştirme
        return this.interpolate(translation, params);
    }

    /**
     * Fallback çeviri getir
     */
    getFallbackTranslation(keys) {
        let translation = this.translations[this.fallbackLocale];

        for (const k of keys) {
            if (translation && translation[k]) {
                translation = translation[k];
            } else {
                return null;
            }
        }

        return translation;
    }

    /**
     * String interpolation
     */
    interpolate(str, params) {
        return str.replace(/{{(\w+)}}/g, (match, key) => {
            return params[key] || match;
        });
    }

    /**
     * Locale değiştir
     */
    async setLocale(locale) {
        if (locale === this.currentLocale) return;

        const success = await this.loadTranslations(locale);
        if (success) {
            // Sayfayı yeniden render et
            this.notifyLocaleChange(locale);
        }
    }

    /**
     * Locale değişikliğini bildir
     */
    notifyLocaleChange(locale) {
        window.dispatchEvent(new CustomEvent('locale:changed', {
            detail: { locale }
        }));
    }

    /**
     * Tarih formatla
     */
    formatDate(date, format = 'short') {
        const options = {
            short: { day: 'numeric', month: 'short', year: 'numeric' },
            long: { day: 'numeric', month: 'long', year: 'numeric' },
            time: { hour: '2-digit', minute: '2-digit' }
        };

        return new Intl.DateTimeFormat(this.currentLocale, options[format]).format(date);
    }

    /**
     * Sayı formatla
     */
    formatNumber(number, options = {}) {
        return new Intl.NumberFormat(this.currentLocale, options).format(number);
    }

    /**
     * Para birimi formatla
     */
    formatCurrency(amount, currency = 'TRY') {
        return new Intl.NumberFormat(this.currentLocale, {
            style: 'currency',
            currency: currency
        }).format(amount);
    }
}

// Singleton instance
export const i18n = new I18n();

// Alpine.js direktifi
if (window.Alpine) {
    Alpine.directive('t', (el, { expression }) => {
        el.textContent = i18n.t(expression);
    });

    Alpine.magic('t', () => {
        return (key, params) => i18n.t(key, params);
    });
}
