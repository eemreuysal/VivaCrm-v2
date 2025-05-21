/**
 * VivaCRM - Alpine.js Dashboard Bileşeni
 * 
 * Dashboard sayfasına özel Alpine.js bileşeni.
 * Veri yükleme, filtreleme ve grafik yönetimi için gerekli tüm işlevleri içerir.
 */

import { createLogger } from '../../core/utils.js';

// Logger oluştur
const logger = createLogger('Dashboard', {
  emoji: '📊'
});

/**
 * Dashboard bileşeni
 * @returns {Object} Alpine.js bileşen nesnesi
 */
export function dashboardComponent() {
  return {
    // Durum değişkenleri
    loading: false,
    currentPeriod: 'month',
    customStartDate: null,
    customEndDate: null,
    charts: {},
    
    // Yaşam döngüsü metodu
    initialize() {
      logger.info('Dashboard bileşeni başlatılıyor...');
      
      // Sunucu tarafından gönderilen verileri veya global değişkeni kullan
      const initData = (window.VivaCRM && window.VivaCRM.dashboardInitData) || window.dashboardInitData;
      
      if (initData) {
        this.currentPeriod = initData.currentPeriod || 'month';
        this.customStartDate = initData.customStartDate || null;
        this.customEndDate = initData.customEndDate || null;
        logger.debug(`Dashboard başlatıldı, periyot: ${this.currentPeriod}`);
      } else {
        logger.warn('Dashboard başlangıç verisi bulunamadı, varsayılanlar kullanılıyor');
      }
      
      // Olay dinleyicilerini kur
      this.setupEventListeners();
      
      // DOM hazır olduğunda grafikleri başlat
      this.$nextTick(() => {
        this.initializeCharts();
      });
    },
    
    // HTMX olay dinleyicileri kurulumu
    setupEventListeners() {
      document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.detail.target.id === 'dashboard-content') {
          this.loading = false;
          this.initializeCharts();
          logger.debug('Dashboard içeriği güncellendi, grafikler yeniden yükleniyor');
        }
      });
      
      document.body.addEventListener('htmx:beforeRequest', (event) => {
        if (event.detail.target.id === 'dashboard-content') {
          this.loading = true;
          logger.debug('Dashboard içeriği yükleniyor...');
        }
      });
      
      // Tema değişikliklerini dinle
      window.addEventListener('vivacrm:theme-changed', () => {
        this.updateChartsTheme();
        logger.debug('Tema değişti, grafik temaları güncelleniyor');
      });
    },
    
    // Seçili periyodu değiştir ve verileri yenile
    setPeriod(period) {
      this.currentPeriod = period;
      logger.debug(`Periyot değiştirildi: ${period}`);
      this.refreshData();
    },
    
    // Dashboard verilerini yenile
    refreshData() {
      this.loading = true;
      
      // HTMX kullanarak dashboard içeriğini yenile
      const dashboardContent = document.getElementById('dashboard-content');
      if (dashboardContent && window.htmx) {
        const periodParams = {
          period: this.currentPeriod
        };
        
        // Özel tarih aralığı parametrelerini ekle (gerekirse)
        if (this.currentPeriod === 'custom' && this.customStartDate && this.customEndDate) {
          periodParams.start_date = this.customStartDate;
          periodParams.end_date = this.customEndDate;
        }
        
        // HTMX isteğini tetikle
        window.htmx.trigger(dashboardContent, 'periodChanged', {
          params: periodParams
        });
        
        logger.debug(`Veriler yenileniyor, periyot: ${this.currentPeriod}`);
      } else {
        logger.error('Dashboard içeriği veya HTMX bulunamadı!');
        this.loading = false;
      }
    },
    
    // Özel tarih aralığını uygula
    applyCustomDateRange() {
      if (this.customStartDate && this.customEndDate) {
        this.currentPeriod = 'custom';
        logger.debug(`Özel tarih aralığı uygulanıyor: ${this.customStartDate} - ${this.customEndDate}`);
        this.refreshData();
      } else {
        logger.warn('Özel tarih aralığı için başlangıç ve bitiş tarihleri gereklidir');
      }
    },
    
    // Grafikleri başlat
    initializeCharts() {
      if (typeof ApexCharts === 'undefined') {
        logger.warn('ApexCharts yüklü değil, CDN\'den yüklemeye çalışılıyor');
        this.loadApexChartsFromCDN();
        return;
      }
      
      logger.info('Dashboard grafikleri başlatılıyor');
      
      // Grafik elementlerini al
      const chartElements = {
        sales: document.getElementById('salesChart'),
        categories: document.getElementById('categoryChart'),
        orders: document.getElementById('ordersChart')
      };
      
      // Grafikleri oluştur
      Object.entries(chartElements).forEach(([name, element]) => {
        if (!element) {
          logger.debug(`${name} grafiği için element bulunamadı, atlanıyor`);
          return;
        }
        
        // Grafik seçeneklerini al
        const options = this.getChartOptions(name);
        
        // Mevcut grafiği yok et
        if (this.charts[name]) {
          this.charts[name].destroy();
          logger.debug(`${name} grafiği yeniden oluşturuluyor`);
        }
        
        // Yeni grafik oluştur
        try {
          this.charts[name] = new ApexCharts(element, options);
          this.charts[name].render();
          logger.debug(`${name} grafiği başarıyla oluşturuldu`);
        } catch (error) {
          logger.error(`${name} grafiği oluşturma hatası: ${error.message}`);
        }
      });
      
      // Grafiklere temayı uygula
      this.updateChartsTheme();
    },
    
    // ApexCharts'ı CDN'den yükle (gerekirse)
    loadApexChartsFromCDN() {
      if (document.querySelector('script[src*="apexcharts"]')) {
        logger.debug('ApexCharts zaten yükleniyor, atlanıyor');
        return; // Zaten yükleniyor
      }
      
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/apexcharts';
      script.async = true;
      script.onload = () => {
        logger.info('ApexCharts CDN\'den yüklendi');
        this.initializeCharts();
      };
      document.head.appendChild(script);
    },
    
    // Grafik seçeneklerini al (grafik türüne göre)
    getChartOptions(chartName) {
      // ThemeManager ile karanlık mod aktif mi kontrol et
      const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
      const isDarkMode = themeManager ? 
        themeManager.currentTheme === 'dark' : 
        (document.documentElement.classList.contains('dark') || 
         document.documentElement.getAttribute('data-theme') === 'dark');
      
      // Ortak grafik seçenekleri
      const commonOptions = {
        chart: {
          fontFamily: 'Inter, sans-serif',
          background: 'transparent',
          toolbar: {
            show: false
          },
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 800,
            dynamicAnimation: {
              enabled: true,
              speed: 350
            }
          }
        },
        theme: {
          mode: isDarkMode ? 'dark' : 'light'
        },
        tooltip: {
          theme: isDarkMode ? 'dark' : 'light',
          y: {
            formatter: function(value) {
              if (chartName === 'sales') {
                return window.formatCurrency ? window.formatCurrency(value) : value;
              }
              return window.formatNumber ? window.formatNumber(value) : value;
            }
          }
        },
        grid: {
          borderColor: isDarkMode ? '#333' : '#e2e8f0',
          strokeDashArray: 3,
          position: 'back'
        }
      };
      
      // Grafik türüne özel seçenekler
      switch (chartName) {
      case 'sales':
        return {
          ...commonOptions,
          chart: {
            ...commonOptions.chart,
            type: 'area',
            height: 350
          },
          series: this.getChartData('sales'),
          colors: ['#3b82f6'],
          fill: {
            type: 'gradient',
            gradient: {
              shadeIntensity: 1,
              opacityFrom: 0.7,
              opacityTo: 0.3,
              stops: [0, 90, 100]
            }
          },
          dataLabels: {
            enabled: false
          },
          stroke: {
            curve: 'smooth',
            width: 3
          },
          xaxis: {
            categories: this.getChartCategories('sales'),
            axisBorder: {
              show: false
            },
            axisTicks: {
              show: false
            }
          },
          yaxis: {
            labels: {
              formatter: function(value) {
                return value >= 1000
                  ? `${(value / 1000).toFixed(1)}K`
                  : value;
              }
            }
          }
        };
        
      case 'categories':
        return {
          ...commonOptions,
          chart: {
            ...commonOptions.chart,
            type: 'donut',
            height: 350
          },
          series: this.getChartData('categories'),
          labels: this.getChartCategories('categories'),
          colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
          legend: {
            position: 'bottom',
            offsetY: 8
          },
          plotOptions: {
            pie: {
              donut: {
                size: '60%',
                labels: {
                  show: true,
                  name: {
                    show: true
                  },
                  value: {
                    show: true,
                    formatter: function(val) {
                      return window.formatNumber ? window.formatNumber(val) : val;
                    }
                  },
                  total: {
                    show: true,
                    showAlways: false,
                    label: 'Toplam',
                    formatter: function(w) {
                      const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                      return window.formatNumber ? window.formatNumber(total) : total;
                    }
                  }
                }
              }
            }
          },
          responsive: [{
            breakpoint: 480,
            options: {
              legend: {
                position: 'bottom'
              }
            }
          }]
        };
        
      case 'orders':
        return {
          ...commonOptions,
          chart: {
            ...commonOptions.chart,
            type: 'bar',
            height: 350
          },
          series: this.getChartData('orders'),
          colors: ['#8b5cf6'],
          plotOptions: {
            bar: {
              borderRadius: 4,
              columnWidth: '50%'
            }
          },
          dataLabels: {
            enabled: false
          },
          xaxis: {
            categories: this.getChartCategories('orders'),
            axisBorder: {
              show: false
            },
            axisTicks: {
              show: false
            }
          },
          yaxis: {
            labels: {
              formatter: function(value) {
                return parseInt(value);
              }
            }
          }
        };
        
      default:
        return commonOptions;
      }
    },
    
    // HTML veri özniteliklerinden grafik verilerini al
    getChartData(chartName) {
      // Element ID'sini oluştur ve veri kümesinden verileri al
      const chartEl = document.getElementById(`${chartName}Chart`);
      if (chartEl && chartEl.dataset.series) {
        try {
          return JSON.parse(chartEl.dataset.series);
        } catch (e) {
          logger.error(`${chartName} grafik verisi ayrıştırma hatası: ${e.message}`);
        }
      }
      
      // Varsayılan veriler
      switch (chartName) {
      case 'sales':
        return [{
          name: 'Satışlar',
          data: [30, 40, 45, 50, 49, 60, 70, 91, 125]
        }];
      case 'categories':
        return [44, 55, 13, 43, 22];
      case 'orders':
        return [{
          name: 'Siparişler',
          data: [10, 15, 20, 25, 30, 35, 40, 45, 50]
        }];
      default:
        return [];
      }
    },
    
    // HTML veri özniteliklerinden grafik kategorilerini al
    getChartCategories(chartName) {
      // Element ID'sini oluştur ve veri kümesinden kategorileri al
      const chartEl = document.getElementById(`${chartName}Chart`);
      if (chartEl && chartEl.dataset.categories) {
        try {
          return JSON.parse(chartEl.dataset.categories);
        } catch (e) {
          logger.error(`${chartName} grafik kategorileri ayrıştırma hatası: ${e.message}`);
        }
      }
      
      // Varsayılan kategoriler
      switch (chartName) {
      case 'sales':
      case 'orders':
        return ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl'];
      case 'categories':
        return ['Elektronik', 'Mobilya', 'Mutfak', 'Giyim', 'Diğer'];
      default:
        return [];
      }
    },
    
    // Grafik temalarını güncelle
    updateChartsTheme() {
      // ThemeManager ile karanlık mod aktif mi kontrol et
      const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
      const isDarkMode = themeManager ? 
        themeManager.currentTheme === 'dark' : 
        (document.documentElement.classList.contains('dark') || 
         document.documentElement.getAttribute('data-theme') === 'dark');
      
      Object.values(this.charts).forEach((chart) => {
        if (chart && typeof chart.updateOptions === 'function') {
          chart.updateOptions({
            theme: {
              mode: isDarkMode ? 'dark' : 'light'
            },
            tooltip: {
              theme: isDarkMode ? 'dark' : 'light'
            },
            grid: {
              borderColor: isDarkMode ? '#333' : '#e2e8f0'
            }
          });
        }
      });
      
      logger.debug(`Grafik temaları güncellendi, tema: ${isDarkMode ? 'dark' : 'light'}`);
    }
  };
}

// ES modül olarak dışa aktar
export default dashboardComponent;