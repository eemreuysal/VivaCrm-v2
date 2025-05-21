/**
 * VivaCRM Dashboard Initialization - Unified Version
 * 
 * Bu dosya dashboard sayfası için gerekli bileşenleri başlatır ve
 * dashboard-components.js'den gelen bileşenleri Alpine.js'e kaydeder.
 * 
 * alpine-unified.js ile uyumlu çalışır.
 */

// Hata ayıklama loglama fonksiyonu
function log(message, type = 'info') {
  const prefix = '📊 Dashboard: ';
  switch(type) {
    case 'error':
      console.error(prefix + message);
      break;
    case 'warn':
      console.warn(prefix + message);
      break;
    default:
      console.log(prefix + message);
  }
}

log('Dashboard bileşenleri başlatılıyor...');

// Dashboard bileşenlerini global olarak tanımlamak için fonksiyon
function initializeDashboardComponents() {
  // Alpine.js yüklü mü kontrol et
  if (!window.Alpine) {
    log('Alpine.js yüklü değil! Lütfen önce Alpine.js scriptinin yüklenmesini sağlayın.', 'error');
    return;
  }

  // VivaCRM objesi kontrol et (alpine-unified.js ile init edilmiş olmalı)
  if (!window.VivaCRM || !window.VivaCRM.alpineInitialized) {
    log('Alpine.js henüz başlatılmamış! Dashboard bileşenleri kaydedilemedi.', 'error');
    
    // Başlatılana kadar bekle ve tekrar dene
    const waitForAlpine = setInterval(() => {
      if (window.VivaCRM && window.VivaCRM.alpineInitialized) {
        clearInterval(waitForAlpine);
        log('Alpine.js hazır, bileşenler kaydediliyor...');
        registerComponentsWithRetry();
      }
    }, 100);
    
    // Maksimum 5 saniye bekle
    setTimeout(() => {
      clearInterval(waitForAlpine);
      if (!window.VivaCRM || !window.VivaCRM.alpineInitialized) {
        log('Alpine.js 5 saniye içinde başlatılamadı.', 'error');
      }
    }, 5000);
    
    return;
  }
  
  // Bileşenleri kaydet
  registerComponentsWithRetry();
  
  // Dashboard bileşenlerini kaydet - tekrar deneme mekanizması ile
  function registerComponentsWithRetry(retryCount = 0, maxRetries = 3) {
    try {
      // dashboard-components.js'den gelen bileşenleri kontrol et
      if (typeof window.dashboardComponent !== 'function' || 
          !window.dashboardComponent().initialize ||
          typeof window.dateFilterComponent !== 'function') {
        
        if (retryCount >= maxRetries) {
          log(`Maksimum deneme sayısına ulaşıldı (${maxRetries}). Dashboard bileşenleri bulunamadı.`, 'error');
          importComponentsAndRetry();
          return;
        }
        
        log(`Dashboard bileşenleri henüz yüklenmemiş. Deneme ${retryCount + 1}/${maxRetries}...`, 'warn');
        
        // 200ms sonra tekrar dene
        setTimeout(() => {
          registerComponentsWithRetry(retryCount + 1, maxRetries);
        }, 200);
        
        return;
      }
      
      log('Alpine.js hazır, bileşenler kaydediliyor...');
      
      // Alpine.js bileşenlerini tanımla
      if (typeof Alpine.data === 'function') {
        Alpine.data('dashboardComponent', window.dashboardComponent);
        Alpine.data('dateFilterComponent', window.dateFilterComponent);
        
        if (window.ordersTableApp) {
          Alpine.data('ordersTableApp', window.ordersTableApp);
        }
        
        log('Dashboard bileşenleri Alpine.js\'e kaydedildi.');
        
        // Sayfada bulunan tüm Alpine.js bileşenlerini yeniden başlat
        if (typeof Alpine.initTree === 'function') {
          Alpine.initTree(document.body);
          log('Alpine.js ağacı yeniden başlatıldı.');
        }
      } else {
        log('Alpine.js data() metodu bulunamadı!', 'error');
      }
      
      // Grafikleri başlat
      setupCharts();
    } catch (error) {
      log('Dashboard bileşenleri kayıt hatası: ' + error.message, 'error');
      console.error(error);
      
      if (retryCount < maxRetries) {
        // 300ms sonra tekrar dene
        setTimeout(() => {
          registerComponentsWithRetry(retryCount + 1, maxRetries);
        }, 300);
      }
    }
  }
  
  // Bileşenler bulunamadıysa, script'i import et ve tekrar dene
  function importComponentsAndRetry() {
    try {
      log('dashboard-components.js manuel olarak yükleniyor...', 'warn');
      
      // Script import et
      import('/static/js/components/dashboard-components.js')
        .then(module => {
          // Module'den bileşenleri global'e aktar
          window.dashboardComponent = module.dashboardComponent;
          window.dateFilterComponent = module.dateFilterComponent;
          window.ordersTableApp = module.ordersTableApp;
          
          log('Dashboard bileşenleri manual olarak import edildi. Kayıt tekrar deneniyor...');
          registerComponentsWithRetry();
        })
        .catch(err => {
          log('Dashboard bileşenleri import hatası: ' + err.message, 'error');
        });
    } catch (error) {
      log('ESM module import hatası: ' + error.message, 'error');
    }
  }
}

/**
 * Dashboard grafiklerini başlat
 */
function setupCharts() {
  log('ApexCharts zaten yüklü, grafikler başlatılıyor...', 'info');
  
  // Sayfa yüklendikten sonra grafikleri başlatmak için
  // Alpine.js dashboardComponent'ine erişmeye çalış
  const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
  
  if (dashboardEl && dashboardEl.__x) {
    log('Dashboard Alpine.js bileşeni bulundu, grafikler başlatılıyor...');
    try {
      dashboardEl.__x.$data.initializeCharts();
    } catch (error) {
      log('Grafik başlatma hatası: ' + error.message, 'error');
    }
  } else {
    log('Dashboard Alpine.js bileşeni henüz hazır değil, biraz sonra tekrar denenecek...', 'warn');
    
    // Daha uzun bekle ve birkaç kez tekrar dene - Alpine.js tamamen başlatılmamış olabilir
    let retryCount = 0;
    const maxRetries = 5;
    const retryInterval = setInterval(() => {
      retryCount++;
      const retryDashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
      
      if (retryDashboardEl && retryDashboardEl.__x) {
        log(`Deneme ${retryCount}: Dashboard Alpine.js bileşeni bulundu, grafikler başlatılıyor...`);
        try {
          retryDashboardEl.__x.$data.initializeCharts();
          clearInterval(retryInterval);
        } catch (error) {
          log(`Deneme ${retryCount}: Grafik başlatma hatası: ` + error.message, 'error');
        }
      } else {
        log(`Deneme ${retryCount}/${maxRetries}: Dashboard Alpine.js bileşeni bulunamadı.`, 'warn');
      }
      
      if (retryCount >= maxRetries) {
        clearInterval(retryInterval);
        log('Maksimum yeniden deneme sayısına ulaşıldı. Grafik başlatma başarısız.', 'error');
        
        // Son çare: Sayfadaki tüm dashboard bileşenlerini yeniden başlatmayı dene
        try {
          if (window.Alpine && typeof window.Alpine.initTree === 'function') {
            window.Alpine.initTree(document.body);
            log('Tüm Alpine.js bileşenleri yeniden başlatıldı, grafikleri tekrar kontrol et.');
            
            // Kısa bir bekleme süresi sonra tekrar dene
            setTimeout(() => {
              const finalRetryEl = document.querySelector('[x-data="dashboardComponent()"]');
              if (finalRetryEl && finalRetryEl.__x) {
                try {
                  finalRetryEl.__x.$data.initializeCharts();
                  log('Son deneme: Grafikler başarıyla başlatıldı!');
                } catch (err) {
                  log('Son deneme: Grafik başlatma hatası: ' + err.message, 'error');
                }
              }
            }, 200);
          }
        } catch (finalError) {
          log('Alpine.js ağacı yeniden başlatılamadı: ' + finalError.message, 'error');
        }
      }
    }, 500);
  }
}

// Sayfa yükleme durumunu kontrol et ve uygun şekilde başlat
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeDashboardComponents);
} else {
  initializeDashboardComponents();
}