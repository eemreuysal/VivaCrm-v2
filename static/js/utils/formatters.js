/**
 * Formatters
 *
 * Veri formatlama için yardımcı fonksiyonlar
 * @module utils/formatters
 */

/**
 * Tarihi formatla
 * @param {string|Date} date - Formatlanacak tarih
 * @param {Object} options - Intl.DateTimeFormat için seçenekler
 * @returns {string} Formatlanmış tarih
 */
export function formatDate(date, options = {}) {
    if (!date) return '';

    const defaultOptions = {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Intl.DateTimeFormat('tr-TR', mergedOptions).format(new Date(date));
}

/**
 * Para birimini formatla
 * @param {number} amount - Formatlanacak miktar
 * @param {string} currency - Para birimi (varsayılan: TRY)
 * @param {Object} options - Intl.NumberFormat için seçenekler
 * @returns {string} Formatlanmış para birimi
 */
export function formatCurrency(amount, currency = 'TRY', options = {}) {
    if (amount === null || amount === undefined) return '';

    const defaultOptions = {
        style: 'currency',
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Intl.NumberFormat('tr-TR', mergedOptions).format(amount);
}

/**
 * Sayıyı formatla
 * @param {number} number - Formatlanacak sayı
 * @param {Object} options - Intl.NumberFormat için seçenekler
 * @returns {string} Formatlanmış sayı
 */
export function formatNumber(number, options = {}) {
    if (number === null || number === undefined) return '';

    const defaultOptions = {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Intl.NumberFormat('tr-TR', mergedOptions).format(number);
}

/**
 * Formatlanmış percent değeri
 * @param {number} value - 0-1 arası değer
 * @param {Object} options - Intl.NumberFormat için seçenekler
 * @returns {string} Formatlanmış yüzde
 */
export function formatPercent(value, options = {}) {
    if (value === null || value === undefined) return '';

    const defaultOptions = {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Intl.NumberFormat('tr-TR', mergedOptions).format(value);
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

export default {
    formatDate,
    formatCurrency,
    formatNumber,
    formatPercent,
    formatFileSize,
    truncateText
};
