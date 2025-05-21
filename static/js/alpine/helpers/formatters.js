/**
 * VivaCRM veri formatlama yardımcı fonksiyonları
 * Alpine.js ile kullanım için optimize edilmiştir
 */

/**
 * Bir sayıyı para birimi formatına dönüştürür
 * 
 * @param {number} amount - Formatlanacak miktar
 * @param {string} [currency='TL'] - Para birimi
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @returns {string} Formatlanmış para birimi
 */
export function currency(amount, currency = 'TRY', locale = 'tr-TR') {
  if (amount === null || amount === undefined) return '';
  
  // String ise sayıya dönüştür
  const numericAmount = typeof amount === 'string' 
    ? parseFloat(amount.replace(',', '.')) 
    : amount;
  
  // Sayı değilse veya geçersizse boş dön
  if (isNaN(numericAmount)) return '';
  
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    currencyDisplay: 'symbol',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numericAmount);
}

/**
 * Sayıyı bin ayırıcılı formata dönüştürür
 * 
 * @param {number} number - Formatlanacak sayı
 * @param {number} [decimals=0] - Ondalık basamak sayısı
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @returns {string} Formatlanmış sayı
 */
export function number(num, decimals = 0, locale = 'tr-TR') {
  if (num === null || num === undefined) return '';
  
  const numericValue = typeof num === 'string'
    ? parseFloat(num.replace(',', '.'))
    : num;
    
  if (isNaN(numericValue)) return '';
  
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(numericValue);
}

/**
 * Tarihi formatlar
 * 
 * @param {string|Date} date - Formatlanacak tarih
 * @param {string} [format='long'] - 'short', 'medium', 'long' formatı
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @returns {string} Formatlanmış tarih
 */
export function date(date, format = 'long', locale = 'tr-TR') {
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
 * Yüzde değeri formatlar
 * 
 * @param {number} value - Formatlanacak değer (örnek: 0.75 => %75)
 * @param {number} [decimals=1] - Ondalık hane sayısı
 * @param {string} [locale='tr-TR'] - Kullanılacak yerelleştirme
 * @returns {string} Formatlanmış yüzde
 */
export function percent(value, decimals = 1, locale = 'tr-TR') {
  if (value === null || value === undefined) return '';
  
  const numericValue = typeof value === 'string'
    ? parseFloat(value.replace(',', '.'))
    : value;
    
  if (isNaN(numericValue)) return '';
  
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(numericValue / 100);
}

/**
 * Dosya boyutunu insan tarafından okunabilir formata dönüştürür
 * 
 * @param {number} bytes - Bayt cinsinden dosya boyutu
 * @param {number} [decimals=2] - Ondalık hane sayısı
 * @returns {string} Formatlanmış dosya boyutu
 */
export function fileSize(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}

// Geriye dönük uyumluluk için eski fonksiyon isimleri
export const formatCurrency = currency;
export const formatNumber = number;
export const formatDate = date;