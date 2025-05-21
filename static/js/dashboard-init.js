/**
 * VivaCRM Dashboard Initialization
 * 
 * Bu dosya dashboard sayfası için gerekli bileşenleri başlatır ve
 * formatlamalar ile grafikler için gerekli işlevleri sağlar.
 */

// Dashboard bileşenlerini global olarak tanımlamak için fonksiyon
function initializeDashboardComponents() {
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
  
  // Alpine.js yüklü mü kontrol et - ayrıca başlatılmış mı kontrol et
  if (!window.Alpine) {
    log('Alpine.js yüklü değil! Lütfen önce Alpine.js scriptinin yüklenmesini sağlayın.', 'error');
    return;
  }

  // Alpine.js başlatılmış mı kontrol et
  if (!window.VivaCRM || !window.VivaCRM.alpineInitialized) {
    log('Alpine.js henüz başlatılmamış! Dashboard bileşenleri kaydedilemedi.', 'error');
    
    // Başlatılana kadar bekle ve tekrar dene
    const waitForAlpine = setInterval(() => {
      if (window.VivaCRM && window.VivaCRM.alpineInitialized) {
        clearInterval(waitForAlpine);
        log('Alpine.js hazır, bileşenler kaydediliyor...');
        registerComponents();
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
  registerComponents();
  
  // Dashboard bileşenlerini kaydet
  function registerComponents() {
    try {
      // Dashboard bileşenlerini global olarak kullanılabilir yap
      if (typeof window.dashboardComponent !== 'function') {
        window.dashboardComponent = createDashboardComponent();
      }
      
      if (typeof window.dateFilterComponent !== 'function') {
        window.dateFilterComponent = createDateFilterComponent();
      }
      
      if (typeof window.ordersTableApp !== 'function') {
        window.ordersTableApp = createOrdersTableApp();
      }
      
      log('Dashboard bileşenleri global olarak kaydedildi.');

      // Alpine.js bileşenlerini tanımla
      if (typeof Alpine.data === 'function') {
        Alpine.data('dashboardComponent', window.dashboardComponent);
        Alpine.data('dateFilterComponent', window.dateFilterComponent);
        Alpine.data('ordersTableApp', window.ordersTableApp);
        
        log('Dashboard bileşenleri Alpine.js\'e kaydedildi.');
        
        // Sayfada bulunan tüm Alpine.js bileşenlerini yeniden başlat
        if (typeof Alpine.initTree === 'function') {
          Alpine.initTree(document.body);
          log('Alpine.js ağacı yeniden başlatıldı.');
        }
      } else {
        log('Alpine.js data() metodu bulunamadı!', 'error');
      }
      
      // HTMX entegrasyonu için olay işleyicileri
      document.body.addEventListener('htmx:afterSwap', function(event) {
        if (event.detail.target.id === 'dashboard-content') {
          log('Dashboard içeriği güncellendi, Alpine.js bileşenleri yeniden başlatılıyor...');
          
          if (typeof Alpine.initTree === 'function') {
            Alpine.initTree(event.detail.target);
          }
        }
      });

      // Grafikleri başlat
      setupCharts();
    } catch (error) {
      log('Dashboard bileşenleri kayıt hatası: ' + error.message, 'error');
      console.error(error);
    }
  }
}

// Sayfa yükleme durumunu kontrol et ve uygun şekilde başlat
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeDashboardComponents);
} else {
  initializeDashboardComponents();
}

/**
 * Dashboard grafiklerini başlat
 */
function setupCharts() {
  // Hata ayıklama loglama fonksiyonu
  function log(message, type = 'info') {
    const prefix = '📈 Charts: ';
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

  // ApexCharts yüklü mü kontrol et  
  if (typeof ApexCharts === 'undefined') {
    log('ApexCharts henüz yüklenmedi, yükleme bekleniyor...');
    
    // ApexCharts'ı manuel olarak yüklemeyi dene
    const script = document.createElement('script');
    script.src = '/static/js/vendor/apexcharts.min.js';
    script.onload = function() {
      log('ApexCharts manuel olarak yüklendi, grafikler başlatılıyor...');
      initializeInitialCharts();
    };
    script.onerror = function() {
      log('ApexCharts yüklenemedi.', 'error');
    };
    document.head.appendChild(script);
  } else {
    log('ApexCharts zaten yüklü, grafikler başlatılıyor...');
    initializeInitialCharts();
  }
}

/**
 * Sayfa ilk yüklendiğinde çizilecek grafikleri başlat
 */
function initializeInitialCharts() {
  // Hata ayıklama loglama fonksiyonu
  function log(message, type = 'info') {
    const prefix = '📊 Charts Init: ';
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

  // Grafikleri başlatmak için setupDashboardCharts fonksiyonunu kullan
  if (typeof window.setupDashboardCharts === 'function') {
    window.setupDashboardCharts();
  } else {
    log('window.setupDashboardCharts fonksiyonu bulunamadı', 'error');

    // Alternatif grafik başlatma
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
}

// Dashboard component oluşturma (fallback için)
function createDashboardComponent() {
  return function() {
    return {
      // Durum değişkenleri
      loading: false,
      currentPeriod: 'month',
      customStartDate: null,
      customEndDate: null,
      charts: {},
      
      // Lifecycle methodları
      initialize() {
        if (window.dashboardInitData) {
          this.currentPeriod = window.dashboardInitData.currentPeriod || 'month';
          this.customStartDate = window.dashboardInitData.customStartDate || null;
          this.customEndDate = window.dashboardInitData.customEndDate || null;
        }
        
        // Event listener'ları kur
        this.setupEventListeners();
        
        // Grafikleri başlat
        this.$nextTick(() => {
          this.initializeCharts();
        });
      },
      
      setupEventListeners() {
        document.body.addEventListener('htmx:afterSwap', (event) => {
          if (event.detail.target.id === 'dashboard-content') {
            this.loading = false;
            this.initializeCharts();
          }
        });
      },
      
      setPeriod(period) {
        this.currentPeriod = period;
        this.refreshData();
      },
      
      refreshData() {
        this.loading = true;
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent && window.htmx) {
          window.htmx.trigger(dashboardContent, 'periodChanged', {
            params: { period: this.currentPeriod }
          });
        }
      },
      
      initializeCharts() {
        if (typeof window.setupDashboardCharts === 'function') {
          window.setupDashboardCharts();
        } else if (typeof ApexCharts !== 'undefined') {
          // Temel grafik başlatma
          console.log('Grafikler başlatılıyor...');
        }
      }
    };
  };
}

// Date filter component oluşturma (fallback için)
function createDateFilterComponent() {
  return function() {
    return {
      showDatePicker: false,
      startDate: null,
      endDate: null,
      
      init() {
        // Ana komponentteki tarih bilgilerini al
        if (this.$root.customStartDate) {
          this.startDate = this.$root.customStartDate;
        }
        
        if (this.$root.customEndDate) {
          this.endDate = this.$root.customEndDate;
        }
      },
      
      toggleDatePicker() {
        this.showDatePicker = !this.showDatePicker;
      },
      
      applyCustomDateRange() {
        if (!this.startDate || !this.endDate) {
          alert('Lütfen başlangıç ve bitiş tarihlerini seçin');
          return;
        }
        
        // Ana komponente değerleri aktar
        this.$root.customStartDate = this.startDate;
        this.$root.customEndDate = this.endDate;
        this.$root.setPeriod('custom');
        
        // Seçici kapat
        this.showDatePicker = false;
      }
    };
  };
}

// Orders table component oluşturma (fallback için)
function createOrdersTableApp() {
  return function() {
    return {
      orders: [],
      filteredOrders: [],
      loading: false,
      searchTerm: '',
      orderStatusFilter: 'all',
      
      init() {
        const ordersTable = document.getElementById('orders-table');
        
        if (ordersTable && ordersTable.dataset.orders) {
          try {
            this.orders = JSON.parse(ordersTable.dataset.orders);
            this.filteredOrders = [...this.orders];
          } catch (e) {
            console.error('Orders data parse error:', e);
            this.orders = [];
            this.filteredOrders = [];
          }
        }
      },
      
      filterOrders() {
        // Status filter
        let result = this.orders;
        
        if (this.orderStatusFilter !== 'all') {
          result = result.filter((order) => order.status === this.orderStatusFilter);
        }
        
        // Search term filter
        if (this.searchTerm.trim() !== '') {
          const term = this.searchTerm.toLowerCase();
          result = result.filter((order) =>
            order.id.toString().includes(term) ||
            order.customer_name.toLowerCase().includes(term)
          );
        }
        
        // Update filtered orders
        this.filteredOrders = result;
      }
    };
  };
}