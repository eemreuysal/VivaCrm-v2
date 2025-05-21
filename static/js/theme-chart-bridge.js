/**
 * VivaCRM v2 - Tema Grafik Köprüsü (Eski yol)
 *
 * Bu dosya yeni tema grafik köprüsüne yönlendirme yapar.
 * Geriye dönük uyumluluk için korunmuştur. Yeni geliştirmelerde
 * doğrudan core/theme-chart-bridge.js kullanılmalıdır.
 */

import chartBridge from './core/theme-chart-bridge.js';

// Sayfa yükleme durumunu kontrol et ve uygun şekilde başlat
if (document.readyState !== 'loading') {
  chartBridge.initialize();
}

export default chartBridge;