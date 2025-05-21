/**
 * VivaCRM v2 - Ortak Format İşlevleri
 * 
 * Bu modül, uygulama genelinde tutarlı formatlama için
 * kullanılacak yardımcı fonksiyonları içerir.
 * 
 * Alpine.js formatları magic helper olarak kaydedilir:
 * - $formatNumber(123) -> "123"
 * - $formatCurrency(123.45) -> "123,45 ₺"
 * - $formatDate('2023-01-01') -> "01.01.2023"
 * - $formatPercent(25) -> "%25"
 */

/**
 * Sayıyı formatla
 * @param {number} number - Formatlanacak sayı
 * @param {number} decimals - Ondalık hane sayısı (varsayılan: 0)
 * @returns {string} Formatlanmış sayı
 */
export function formatNumber(number, decimals = 0) {
  if (number === null || number === undefined) return '';
  
  return new Intl.NumberFormat('tr-TR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(number);
}

/**
 * Para birimini formatla
 * @param {number} amount - Formatlanacak miktar
 * @param {string} currency - Para birimi (varsayılan: TRY)
 * @returns {string} Formatlanmış para birimi
 */
export function formatCurrency(amount, currency = 'TRY') {
  if (amount === null || amount === undefined) return '';
  
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * Tarihi formatla
 * @param {string|Date} date - Formatlanacak tarih
 * @param {string} format - Format tipi: 'short', 'medium', 'long' (varsayılan: 'short')
 * @returns {string} Formatlanmış tarih
 */
export function formatDate(date, format = 'short') {
  if (!date) return '';
  
  try {
    const options = {
      short: { day: '2-digit', month: '2-digit', year: 'numeric' },
      medium: { day: '2-digit', month: 'short', year: 'numeric' },
      long: { day: '2-digit', month: 'long', year: 'numeric' }
    };
    
    return new Date(date).toLocaleDateString('tr-TR', options[format] || options.short);
  } catch (e) {
    return date;
  }
}

/**
 * Yüzdeyi formatla
 * @param {number} value - Formatlanacak değer (0-100 arası)
 * @param {number} decimals - Ondalık hane sayısı (varsayılan: 1)
 * @returns {string} Formatlanmış yüzde
 */
export function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined) return '';
  
  const numericValue = typeof value === 'string'
    ? parseFloat(value.replace(',', '.'))
    : value;
    
  if (isNaN(numericValue)) return '';
  
  return new Intl.NumberFormat('tr-TR', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(numericValue / 100);
}

/**
 * Tüm format fonksiyonlarını tek bir objede dışa aktar
 */
export const formatters = {
  formatNumber,
  formatCurrency,
  formatDate,
  formatPercent
};

/**
 * Alpine.js formatters'i magic methodlar olarak kaydeder
 */
export function registerFormatHelpers() {
  if (!window.Alpine || typeof window.Alpine.magic !== 'function') {
    console.warn('Alpine.js bulunamadı, format yardımcıları kaydedilemedi.');
    return;
  }
  
  // Global olarak da eriş
  window.formatNumber = formatNumber;
  window.formatCurrency = formatCurrency;
  window.formatDate = formatDate;
  window.formatPercent = formatPercent;
  window.formatters = formatters;
  
  // Alpine magic methodları
  Alpine.magic('formatNumber', () => formatNumber);
  Alpine.magic('formatCurrency', () => formatCurrency);
  Alpine.magic('formatDate', () => formatDate);
  Alpine.magic('formatPercent', () => formatPercent);
  
  console.log('Format yardımcıları başarıyla kaydedildi');
}

export default formatters;