/**
 * VivaCRM Global Components
 * 
 * Bu dosya, tüm sayfalarda kullanılan global Alpine.js bileşenlerini ve
 * yardımcı fonksiyonları tanımlar. Sayfa yüklenmeden önce dahil edilmelidir.
 */

// Global bileşenleri tanımla - Window objesine bağla
(function() {
  // Hata ayıklama loglama fonksiyonu
  window.vivaLog = function(message, type = 'info') {
    const prefix = '🌍 Global: ';
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
  };

  // Tema Store - Alpine.store('theme') için global tanım
  // Merkezi ThemeManager'a bağlanır, bağlanamadığında fallback kullanır
  window.themeStore = {
    // Başlangıç durumları - ThemeManager varsa güncellenecek
    darkMode: localStorage.getItem('vivacrm-theme') === 'dark',
    systemPreference: window.matchMedia('(prefers-color-scheme: dark)').matches,
    
    init() {
      window.vivaLog('Theme store başlatılıyor...');
      
      // Merkezi ThemeManager var mı diye kontrol et
      const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
      
      if (themeManager) {
        // ThemeManager ile entegre çalış
        window.vivaLog('ThemeManager bulundu, entegrasyon yapılıyor');
        
        // Başlangıç değerlerini ThemeManager'dan al
        this.darkMode = themeManager.currentTheme === 'dark';
        this.systemPreference = themeManager.systemPreference;
        
        // ThemeManager değişikliklerini dinle
        themeManager.subscribe((theme) => {
          this.darkMode = theme === 'dark';
          // Alpine.js store güncellendi bilgisini yay (opsiyonel)
          if (window.Alpine && Alpine.store('theme')) {
            Alpine.store('theme').darkMode = this.darkMode;
          }
        });
      } else {
        // ThemeManager yoksa kendi başlatmamızı yap
        window.vivaLog('ThemeManager bulunamadı, bağımsız çalışma kullanılıyor', 'warn');
        
        if (localStorage.getItem('vivacrm-theme') === null) {
          this.useSystemPreference();
        } else {
          this.applyTheme(this.darkMode ? 'dark' : 'light');
        }
        
        // Sistem tercihi değişimini izle
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
          if (localStorage.getItem('vivacrm-theme-source') === 'system') {
            this.darkMode = e.matches;
            this.applyTheme(this.darkMode ? 'dark' : 'light');
          }
        });
      }
    },
    
    toggle() {
      window.vivaLog('Tema değiştiriliyor: ' + (this.darkMode ? 'açık' : 'koyu'));
      
      // Merkezi ThemeManager var mı diye kontrol et
      const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
      
      if (themeManager) {
        // ThemeManager üzerinden değiştir
        themeManager.toggleTheme();
        // Not: ThemeManager zaten tetikleyeceği için subscribe ile this.darkMode güncellenecek
      } else {
        // Kendi başımıza değiştirme
        this.darkMode = !this.darkMode;
        localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
        localStorage.setItem('vivacrm-theme-source', 'manual');
        this.applyTheme(this.darkMode ? 'dark' : 'light');
        
        // Tema değişikliği olayını tetikle
        document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', {
          detail: { 
            theme: this.darkMode ? 'dark' : 'light', 
            darkMode: this.darkMode,
            source: 'themeStore'
          }
        }));
      }
    },
    
    useSystemPreference() {
      // Merkezi ThemeManager var mı diye kontrol et
      const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
      
      if (themeManager) {
        // ThemeManager üzerinden sistem tercihini kullan
        themeManager.useSystemPreference();
      } else {
        // Kendi başımıza sistem tercihini kullan
        this.darkMode = this.systemPreference;
        localStorage.setItem('vivacrm-theme-source', 'system');
        localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
        this.applyTheme(this.darkMode ? 'dark' : 'light');
      }
    },
    
    applyTheme(theme) {
      // Bu metod yalnızca ThemeManager olmadığında kullanılır
      if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'vivacrmDark');
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.setAttribute('data-theme', 'vivacrm');
        document.documentElement.classList.remove('dark');
      }
    }
  };

  // Notification bileşeni 
  window.notificationComponent = function() {
    return {
      notificationOpen: false,
      
      toggle() {
        this.notificationOpen = !this.notificationOpen;
      },
      
      close() {
        this.notificationOpen = false;
      }
    };
  };

  // Format yardımcıları
  window.formatNumber = function(number, decimals = 0) {
    if (number === null || number === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(number);
  };
  
  window.formatCurrency = function(amount) {
    if (amount === null || amount === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };
  
  window.formatDate = function(date, format = 'short') {
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
  };
  
  window.formatPercent = function(value, decimals = 1) {
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
  };

  // Sayfa yüklendiğinde theme store'u başlat
  document.addEventListener('DOMContentLoaded', function() {
    // Tema değişikliğini uygula
    window.themeStore.init();
    
    // Alpine.js yüklü mü kontrol et
    if (window.Alpine) {
      // Alpine ile tanımla
      Alpine.store('theme', window.themeStore);
      Alpine.data('notificationComponent', window.notificationComponent);
      
      // Format fonksiyonlarını Alpine.js magic helper olarak kaydet
      if (typeof Alpine.magic === 'function') {
        Alpine.magic('formatNumber', () => window.formatNumber);
        Alpine.magic('formatCurrency', () => window.formatCurrency);
        Alpine.magic('formatDate', () => window.formatDate);
        Alpine.magic('formatPercent', () => window.formatPercent);
      }
      
      window.vivaLog('Global bileşenler Alpine.js\'e kaydedildi');
    } else {
      window.vivaLog('Alpine.js yüklü değil, global bileşenler yalnızca window üzerinde tanımlandı', 'warn');
    }
  });

  // Dashboard bileşenlerini de global olarak tanımla (dashboard sayfalarında kullanılabilir)
  window.dashboardComponent = function() {
    return {
      // Durum değişkenleri
      loading: false,
      currentPeriod: 'month',
      customStartDate: null,
      customEndDate: null,
      charts: {},
      
      // Yaşam döngüsü metotları
      initialize() {
        // Sunucudan gönderilen başlangıç verilerini kullan
        const initData = window.dashboardInitData || {
          currentPeriod: 'month',
          customStartDate: null,
          customEndDate: null
        };
        
        this.currentPeriod = initData.currentPeriod || 'month';
        this.customStartDate = initData.customStartDate || null;
        this.customEndDate = initData.customEndDate || null;
        
        // HTMX olaylarını dinle
        this.setupEventListeners();
        
        // Grafikleri yükle (DOM hazır olduğunda)
        this.$nextTick(() => {
          this.initializeCharts();
        });
      },
      
      /**
       * Olay dinleyicilerini ayarla
       */
      setupEventListeners() {
        // HTMX olaylarını dinle
        document.body.addEventListener('htmx:afterSwap', (event) => {
          if (event.detail.target.id === 'dashboard-content') {
            this.loading = false;
            this.initializeCharts();
          }
        });
        
        document.body.addEventListener('htmx:beforeRequest', (event) => {
          if (event.detail.target.id === 'dashboard-content') {
            this.loading = true;
          }
        });
        
        // Tema değişikliği olayını dinle
        document.addEventListener('vivacrm:theme-changed', () => {
          this.updateChartsTheme();
        });
      },
      
      /**
       * Seçilen dönemi değiştir ve verileri yenile
       */
      setPeriod(period) {
        this.currentPeriod = period;
        this.refreshData();
      },
      
      /**
       * Dashboard verilerini yenile
       */
      refreshData() {
        this.loading = true;
        
        // HTMX ile dashboard içeriğini güncelle
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent && window.htmx) {
          const periodParams = {
            period: this.currentPeriod
          };
          
          // Özel tarih aralığı için parametreler ekle
          if (this.currentPeriod === 'custom' && this.customStartDate && this.customEndDate) {
            periodParams.start_date = this.customStartDate;
            periodParams.end_date = this.customEndDate;
          }
          
          // HTMX values değerini güncelle ve tetikle
          window.htmx.trigger(dashboardContent, 'periodChanged', {
            params: periodParams
          });
        }
      },
      
      /**
       * Grafikleri başlat
       */
      initializeCharts() {
        if (typeof ApexCharts === 'undefined') {
          console.log('ApexCharts yüklü değil, grafikler başlatılamadı');
          return;
        }
        
        // Temel uygulama - yalnızca örnek amaçlı
        console.log('Grafikler başlatılıyor...');
        
        // Tema değişikliklerini uygula
        this.updateChartsTheme();
      },
      
      /**
       * Grafik temalarını güncelle
       */
      updateChartsTheme() {
        // Merkezi ThemeManager var mı diye kontrol et
        const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
        const isDarkMode = themeManager ? 
          themeManager.currentTheme === 'dark' : 
          (document.documentElement.classList.contains('dark') || 
           document.documentElement.getAttribute('data-theme') === 'dark' ||
           document.documentElement.getAttribute('data-theme') === 'vivacrmDark');
        
        Object.values(this.charts).forEach((chart) => {
          if (chart && typeof chart.updateOptions === 'function') {
            chart.updateOptions({
              theme: {
                mode: isDarkMode ? 'dark' : 'light'
              }
            });
          }
        });
      },
      
      /**
       * Tarih formatla
       */
      formatDate(date) {
        return window.formatDate(date);
      },
      
      /**
       * Para birimi formatla
       */
      formatCurrency(amount) {
        return window.formatCurrency(amount);
      },
      
      /**
       * Sayı formatla
       */
      formatNumber(number) {
        return window.formatNumber(number);
      }
    };
  };
  
  // Tarih filtresi bileşeni
  window.dateFilterComponent = function() {
    return {
      showDatePicker: false,
      startDate: null,
      endDate: null,
      
      init() {
        if (this.$root.customStartDate) {
          this.startDate = this.$root.customStartDate;
        }
        
        if (this.$root.customEndDate) {
          this.endDate = this.$root.customEndDate;
        }
      },
      
      toggleDatePicker() {
        this.showDatePicker = !this.showDatePicker;
      }
    };
  };
})();