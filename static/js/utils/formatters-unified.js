/**
 * VivaCRM veri formatlama yardımcı fonksiyonları
 *
 * Birleştirilmiş, tüm uygulama için merkezi formatlama yardımcı fonksiyonları.
 * Hem doğrudan kullanım hem de Alpine.js magic entegrasyonu için uygun.
 */

/**
 * Bir sayıyı para birimi formatına dönüştürür
 *
 * @param {number} amount - Formatlanacak miktar
 * @param {string} [currency='TRY'] - Para birimi
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @param {Object} [options={}] - Intl.NumberFormat için ek seçenekler
 * @returns {string} Formatlanmış para birimi
 */
export function formatCurrency(amount, currency = 'TRY', locale = 'tr-TR', options = {}) {
    if (amount === null || amount === undefined) return '';

    // String ise sayıya dönüştür
    const numericAmount = typeof amount === 'string'
        ? parseFloat(amount.replace(',', '.'))
        : amount;

    // Sayı değilse veya geçersizse boş dön
    if (isNaN(numericAmount)) return '';

    const defaultOptions = {
        style: 'currency',
        currency: currency,
        currencyDisplay: 'symbol',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Intl.NumberFormat(locale, mergedOptions).format(numericAmount);
}

/**
 * Sayıyı bin ayırıcılı formata dönüştürür
 *
 * @param {number} number - Formatlanacak sayı
 * @param {number} [decimals=0] - Ondalık basamak sayısı
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @param {Object} [options={}] - Intl.NumberFormat için ek seçenekler
 * @returns {string} Formatlanmış sayı
 */
export function formatNumber(num, decimals = 0, locale = 'tr-TR', options = {}) {
    if (num === null || num === undefined) return '';

    const numericValue = typeof num === 'string'
        ? parseFloat(num.replace(',', '.'))
        : num;

    if (isNaN(numericValue)) return '';

    const defaultOptions = {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Intl.NumberFormat(locale, mergedOptions).format(numericValue);
}

/**
 * Tarihi formatlar
 *
 * @param {string|Date} date - Formatlanacak tarih
 * @param {string|Object} [format='long'] - 'short', 'medium', 'long' formatı veya Intl.DateTimeFormat seçenekleri
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @returns {string} Formatlanmış tarih
 */
export function formatDate(date, format = 'long', locale = 'tr-TR') {
    if (!date) return '';

    let dateObj;

    if (typeof date === 'string') {
    // ISO string veya yyyy-mm-dd formatı
        dateObj = new Date(date);
    } else if (date instanceof Date) {
        dateObj = date;
    } else {
        return '';
    }

    // Tarih geçersizse boş dön
    if (isNaN(dateObj.getTime())) {
        return '';
    }

    try {
    // Eğer format bir nesne ise, doğrudan options olarak kullan
        if (typeof format === 'object') {
            return dateObj.toLocaleDateString(locale, format);
        }

        switch (format) {
        case 'short':
            return dateObj.toLocaleDateString(locale, {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        case 'medium':
            return dateObj.toLocaleDateString(locale, {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            });
        case 'time':
            return dateObj.toLocaleTimeString(locale, {
                hour: '2-digit',
                minute: '2-digit'
            });
        case 'datetime':
            return dateObj.toLocaleDateString(locale, {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        case 'long':
        default:
            return dateObj.toLocaleDateString(locale, {
                day: '2-digit',
                month: 'long',
                year: 'numeric'
            });
        }
    } catch (e) {
        console.error('Tarih formatlama hatası:', e);
        return date.toString();
    }
}

/**
 * Formatlanmış percent değeri
 *
 * @param {number} value - 0-1 arası değer (0.75 = %75) veya 0-100 arası değer
 * @param {number} [decimals=1] - Ondalık basamak sayısı
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @param {boolean} [isRatio=true] - Değer 0-1 arasında bir oran mı yoksa 0-100 arası bir yüzde mi
 * @returns {string} Formatlanmış yüzde
 */
export function formatPercent(value, decimals = 1, locale = 'tr-TR', isRatio = true) {
    if (value === null || value === undefined) return '';

    const numericValue = typeof value === 'string'
        ? parseFloat(value.replace(',', '.'))
        : value;

    if (isNaN(numericValue)) return '';

    // Değer 0-100 arasında verilmişse 0-1'e çevir
    const normalizedValue = isRatio ? numericValue : numericValue / 100;

    return new Intl.NumberFormat(locale, {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(normalizedValue);
}

/**
 * Dosya boyutunu formatla
 * @param {number} bytes - Byte olarak boyut
 * @param {number} decimals - Ondalık basamak sayısı
 * @returns {string} Formatlanmış dosya boyutu (KB, MB, GB)
 */
export function formatFileSize(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

/**
 * Metni kısalt
 * @param {string} text - Kısaltılacak metin
 * @param {number} maxLength - Maksimum uzunluk
 * @param {string} suffix - Kısaltma sonunda gösterilecek metin
 * @returns {string} Kısaltılmış metin
 */
export function truncateText(text, maxLength = 50, suffix = '...') {
    if (!text || text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}${suffix}`;
}

/**
 * HTML karakterlerini escape eder
 * @param {string} html - Escape edilecek metin
 * @returns {string} Escape edilmiş metin
 */
export function escapeHtml(html) {
    if (!html) return '';

    return String(html)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Geriye dönük uyumluluk için kısa isimler
export const currency = formatCurrency;
export const number = formatNumber;
export const date = formatDate;
export const percent = formatPercent;
export const fileSize = formatFileSize;
export const truncate = truncateText;

// Tüm formatters'ı default export et
export default {
    formatCurrency,
    formatNumber,
    formatDate,
    formatPercent,
    formatFileSize,
    truncateText,
    escapeHtml,
    // Kısa isimler
    currency,
    number,
    date,
    percent,
    fileSize,
    truncate
};
