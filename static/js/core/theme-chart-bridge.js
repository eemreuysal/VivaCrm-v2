/**
 * VivaCRM - Tema ve Grafik Entegrasyonu
 * 
 * Bu modül, tema değişikliklerini grafik sistemiyle senkronize eder.
 * ThemeManager ile ApexCharts arasında bir köprü görevi görür.
 */

import themeManager from './theme-store.js';

/**
 * Tema ve grafik sistemi arasındaki köprüyü başlat
 */
function initializeThemeChartBridge() {
  // ThemeManager'dan mevcut tema bilgisini al
  const isDarkMode = themeManager.currentTheme === 'dark';
  
  // İlk grafik güncellemesini yap
  updateChartsTheme(isDarkMode);
  
  // ThemeManager'dan değişiklikleri dinle
  themeManager.subscribe((theme) => {
    updateChartsTheme(theme === 'dark');
  });
  
  console.log('Tema-Grafik köprüsü başlatıldı');
}

/**
 * Grafiklerin temasını güncelle
 * @param {boolean} isDarkMode - Koyu tema modu aktif mi
 */
function updateChartsTheme(isDarkMode) {
  // Chart System API'ı varsa kullan
  if (window.VivaCRM && window.VivaCRM.ChartSystem) {
    window.VivaCRM.ChartSystem.updateChartsTheme(isDarkMode);
    return;
  }
  
  // Dashboard component Alpine.js verisi varsa kullan
  const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
  if (dashboardEl && dashboardEl.__x) {
    if (typeof dashboardEl.__x.$data.updateChartsTheme === 'function') {
      dashboardEl.__x.$data.updateChartsTheme(isDarkMode);
      return;
    }
  }
  
  // ApexCharts doğrudan güncellemek için
  if (typeof ApexCharts !== 'undefined') {
    // Tema güncellenecek ayarlar
    const themeOptions = {
      theme: {
        mode: isDarkMode ? 'dark' : 'light'
      },
      tooltip: {
        theme: isDarkMode ? 'dark' : 'light'
      },
      grid: {
        borderColor: isDarkMode ? '#333' : '#e2e8f0'
      }
    };
    
    // Chart elementleri bul ve güncelle
    document.querySelectorAll('[id$="Chart"]').forEach(chartEl => {
      if (chartEl.chart && typeof chartEl.chart.updateOptions === 'function') {
        chartEl.chart.updateOptions(themeOptions);
      }
    });
  }
}

// DOM hazır olduğunda başlat
document.addEventListener('DOMContentLoaded', initializeThemeChartBridge);

export default {
  initialize: initializeThemeChartBridge,
  updateChartsTheme
};