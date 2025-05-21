/**
 * VivaCRM Dashboard Globals
 * 
 * Bu dosya, dashboard için gerekli bileşenleri ve yardımcı fonksiyonları global olarak tanımlar.
 * Her sayfada dahil edilerek Alpine.js hata vermesini önler ve modül yüklemesi olmadan çalışır.
 */

// Hata ayıklama loglama fonksiyonu
window.dashboardLog = function(message, type = 'info') {
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
};

// Ana dashboard store'unu oluştur
window.dashboardStore = {
  // Durum değişkenleri
  loading: false,
  currentPeriod: 'month',
  customStartDate: null,
  customEndDate: null,
  salesChart: null,
  categoryChart: null,
  ordersChart: null,
  
  // HTMX tetikleme fonksiyonları
  triggerRefresh() {
    this.loading = true;
    const dashboardContent = document.getElementById('dashboard-content');
    if (dashboardContent && window.htmx) {
      const params = new URLSearchParams();
      params.set('period', this.currentPeriod);
      
      if (this.currentPeriod === 'custom' && this.customStartDate && this.customEndDate) {
        params.set('start_date', this.customStartDate);
        params.set('end_date', this.customEndDate);
      }
      
      window.htmx.trigger(dashboardContent, 'periodChanged', {
        params: { period: this.currentPeriod }
      });
    }
  }
};

// Dashboard Component
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
      // Store'dan değerleri al
      this.loading = window.dashboardStore.loading;
      
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
      if (typeof window.setupDashboardCharts === 'function') {
        window.setupDashboardCharts();
      }
    },
    
    // Olay dinleyicilerini ayarla
    setupEventListeners() {
      // HTMX olaylarını dinle
      document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.detail.target.id === 'dashboard-content') {
          this.loading = false;
          window.dashboardStore.loading = false;
          
          // Grafikleri güncelle
          setTimeout(() => {
            if (typeof window.setupDashboardCharts === 'function') {
              window.setupDashboardCharts();
            }
          }, 100);
        }
      });
      
      document.body.addEventListener('htmx:beforeRequest', (event) => {
        if (event.detail.target.id === 'dashboard-content') {
          this.loading = true;
          window.dashboardStore.loading = true;
        }
      });
    },
    
    // Seçilen dönemi değiştir ve verileri yenile
    setPeriod(period) {
      this.currentPeriod = period;
      window.dashboardStore.currentPeriod = period;
      this.refreshData();
    },
    
    // Dashboard verilerini yenile
    refreshData() {
      this.loading = true;
      window.dashboardStore.loading = true;
      
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
    
    // Grafikleri başlat
    initializeCharts() {
      if (typeof window.setupDashboardCharts === 'function') {
        window.setupDashboardCharts();
      }
    },
    
    // Tema değişikliği için grafikleri güncelle
    updateChartsTheme() {
      const isDark = document.documentElement.classList.contains('dark') ||
                   document.documentElement.getAttribute('data-theme') === 'dark';
      
      Object.values(this.charts).forEach((chart) => {
        if (chart && typeof chart.updateOptions === 'function') {
          chart.updateOptions({
            theme: {
              mode: isDark ? 'dark' : 'light'
            },
            tooltip: {
              theme: isDark ? 'dark' : 'light'
            },
            grid: {
              borderColor: isDark ? '#333' : '#e2e8f0'
            }
          });
        }
      });
    },
    
    // Tarih formatla
    formatDate(date) {
      if (!date) return '';
      
      try {
        return new Date(date).toLocaleDateString('tr-TR', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      } catch (e) {
        return date;
      }
    },
    
    // Para birimi formatla
    formatCurrency(amount) {
      return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY'
      }).format(amount);
    },
    
    // Sayı formatla
    formatNumber(number) {
      return new Intl.NumberFormat('tr-TR').format(number);
    }
  };
};

// Date Filter Component
window.dateFilterComponent = function() {
  return {
    // Durum değişkenleri
    showDatePicker: false,
    startDate: null,
    endDate: null,
    
    // Bileşen başlatma
    init() {
      // Ana komponentteki tarih bilgilerini al
      if (this.$root.customStartDate) {
        this.startDate = this.$root.customStartDate;
      }
      
      if (this.$root.customEndDate) {
        this.endDate = this.$root.customEndDate;
      }
    },
    
    // Tarih seçiciyi aç/kapat
    toggleDatePicker() {
      this.showDatePicker = !this.showDatePicker;
    },
    
    // Seçilen tarih aralığını uygula
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

// Dashboard Charts Setup
window.setupDashboardCharts = function() {
  // ApexCharts yüklü değilse çık
  if (typeof ApexCharts === 'undefined') {
    console.error('ApexCharts is not loaded');
    return;
  }
  
  // Tema modunu kontrol et
  const isDark = document.documentElement.classList.contains('dark') ||
               document.documentElement.getAttribute('data-theme') === 'dark';
  
  // Satış grafiği
  const salesChart = document.getElementById('salesChart');
  if (salesChart) {
    try {
      // Veri kontrol et
      let salesData = [];
      let salesLabels = [];
      
      // Dataset attribute JSON parse et
      if (salesChart.dataset.series) {
        try {
          salesData = JSON.parse(salesChart.dataset.series);
        } catch (e) {
          console.error('Sales chart series parse error:', e);
          salesData = [
            {
              name: 'Satışlar',
              data: [3500, 4200, 5100, 4800, 5900, 6300, 7200, 8100, 7500]
            }
          ];
        }
      } else {
        salesData = [
          {
            name: 'Satışlar',
            data: [3500, 4200, 5100, 4800, 5900, 6300, 7200, 8100, 7500]
          }
        ];
      }
      
      // Kategorileri parse et
      if (salesChart.dataset.categories) {
        try {
          salesLabels = JSON.parse(salesChart.dataset.categories);
        } catch (e) {
          console.error('Sales chart categories parse error:', e);
          salesLabels = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl'];
        }
      } else {
        salesLabels = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl'];
      }
      
      // Grafik oluştur
      const salesOptions = {
        chart: {
          type: 'area',
          height: 350,
          fontFamily: 'Inter, sans-serif',
          toolbar: { show: false },
          animations: { enabled: true }
        },
        dataLabels: { enabled: false },
        stroke: { curve: 'smooth', width: 2 },
        series: salesData,
        colors: ['#22c55e'],
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.7,
            opacityTo: 0.3,
            stops: [0, 90, 100]
          }
        },
        xaxis: { 
          categories: salesLabels,
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          labels: {
            formatter: function(value) {
              return value >= 1000 ? `${(value / 1000).toFixed(1)}K` : value;
            }
          }
        },
        theme: { mode: isDark ? 'dark' : 'light' },
        tooltip: { theme: isDark ? 'dark' : 'light' }
      };
      
      // Mevcut grafiği temizle
      if (window.dashboardStore.salesChart) {
        window.dashboardStore.salesChart.destroy();
      }
      
      // Yeni grafik oluştur
      window.dashboardStore.salesChart = new ApexCharts(salesChart, salesOptions);
      window.dashboardStore.salesChart.render();
    } catch (error) {
      console.error('Sales Chart Error:', error);
    }
  }
  
  // Kategori grafiği
  const categoryChart = document.getElementById('categoryChart');
  if (categoryChart) {
    try {
      // Veri kontrol et
      let categoryData = [];
      let categoryLabels = [];
      
      // Dataset attribute JSON parse et
      if (categoryChart.dataset.series) {
        try {
          categoryData = JSON.parse(categoryChart.dataset.series);
        } catch (e) {
          console.error('Category chart series parse error:', e);
          categoryData = [44, 55, 13, 43, 22];
        }
      } else {
        categoryData = [44, 55, 13, 43, 22];
      }
      
      // Kategorileri parse et
      if (categoryChart.dataset.categories) {
        try {
          categoryLabels = JSON.parse(categoryChart.dataset.categories);
        } catch (e) {
          console.error('Category chart categories parse error:', e);
          categoryLabels = ['Elektronik', 'Mobilya', 'Giyim', 'Gıda', 'Diğer'];
        }
      } else {
        categoryLabels = ['Elektronik', 'Mobilya', 'Giyim', 'Gıda', 'Diğer'];
      }
      
      // Grafik oluştur
      const categoryOptions = {
        chart: {
          type: 'donut',
          height: 350,
          fontFamily: 'Inter, sans-serif'
        },
        series: categoryData,
        labels: categoryLabels,
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
                name: { show: true },
                value: {
                  show: true,
                  formatter: function(val) {
                    return new Intl.NumberFormat('tr-TR').format(val);
                  }
                },
                total: {
                  show: true,
                  showAlways: false,
                  label: 'Toplam',
                  formatter: function(w) {
                    const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                    return new Intl.NumberFormat('tr-TR').format(total);
                  }
                }
              }
            }
          }
        },
        theme: { mode: isDark ? 'dark' : 'light' },
        tooltip: { theme: isDark ? 'dark' : 'light' }
      };
      
      // Mevcut grafiği temizle
      if (window.dashboardStore.categoryChart) {
        window.dashboardStore.categoryChart.destroy();
      }
      
      // Yeni grafik oluştur
      window.dashboardStore.categoryChart = new ApexCharts(categoryChart, categoryOptions);
      window.dashboardStore.categoryChart.render();
    } catch (error) {
      console.error('Category Chart Error:', error);
    }
  }
  
  // Sipariş grafiği
  const ordersChart = document.getElementById('ordersChart');
  if (ordersChart) {
    try {
      // Veri kontrol et
      let ordersData = [];
      let ordersLabels = [];
      
      // Dataset attribute JSON parse et
      if (ordersChart.dataset.series) {
        try {
          ordersData = JSON.parse(ordersChart.dataset.series);
        } catch (e) {
          console.error('Orders chart series parse error:', e);
          ordersData = [
            {
              name: 'Siparişler',
              data: [49, 62, 35, 52, 38, 70, 41]
            }
          ];
        }
      } else {
        ordersData = [
          {
            name: 'Siparişler',
            data: [49, 62, 35, 52, 38, 70, 41]
          }
        ];
      }
      
      // Kategorileri parse et
      if (ordersChart.dataset.categories) {
        try {
          ordersLabels = JSON.parse(ordersChart.dataset.categories);
        } catch (e) {
          console.error('Orders chart categories parse error:', e);
          ordersLabels = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
        }
      } else {
        ordersLabels = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
      }
      
      // Grafik oluştur
      const ordersOptions = {
        chart: {
          type: 'bar',
          height: 350,
          fontFamily: 'Inter, sans-serif',
          toolbar: { show: false }
        },
        series: ordersData,
        colors: ['#8b5cf6'],
        plotOptions: {
          bar: {
            borderRadius: 4,
            columnWidth: '50%'
          }
        },
        dataLabels: { enabled: false },
        xaxis: {
          categories: ordersLabels,
          axisBorder: { show: false },
          axisTicks: { show: false }
        },
        yaxis: {
          labels: {
            formatter: function(value) {
              return parseInt(value);
            }
          }
        },
        theme: { mode: isDark ? 'dark' : 'light' },
        tooltip: { theme: isDark ? 'dark' : 'light' }
      };
      
      // Mevcut grafiği temizle
      if (window.dashboardStore.ordersChart) {
        window.dashboardStore.ordersChart.destroy();
      }
      
      // Yeni grafik oluştur
      window.dashboardStore.ordersChart = new ApexCharts(ordersChart, ordersOptions);
      window.dashboardStore.ordersChart.render();
    } catch (error) {
      console.error('Orders Chart Error:', error);
    }
  }
};

// Tema değişikliği olayını dinle
document.addEventListener('vivacrm:theme-changed', function() {
  // Grafiklerin temalarını güncelle
  if (window.dashboardStore) {
    setTimeout(() => {
      window.setupDashboardCharts();
    }, 100);
  }
});

// Sipariş tablosu bileşeni
window.ordersTableApp = function() {
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
          order.customer_name.toLowerCase().includes(term) ||
          order.total_amount.toString().includes(term)
        );
      }
      
      // Update filtered orders
      this.filteredOrders = result;
    },
    
    getStatusClass(status) {
      const statusClasses = {
        'pending': 'badge-warning',
        'processing': 'badge-info',
        'completed': 'badge-success',
        'cancelled': 'badge-error',
        'refunded': 'badge-neutral'
      };
      
      return statusClasses[status] || 'badge-secondary';
    },
    
    viewOrderDetails(orderId) {
      window.location.href = `/orders/${orderId}/`;
    }
  };
};

// Alpine.js global fonksiyonları
if (window.Alpine) {
  // Dashboard bileşenlerini Alpine'a kaydet
  window.Alpine.data('dashboardComponent', window.dashboardComponent);
  window.Alpine.data('dateFilterComponent', window.dateFilterComponent);
  window.Alpine.data('ordersTableApp', window.ordersTableApp);
  
  // Bileşenleri hazır olduğunda bildir
  document.addEventListener('DOMContentLoaded', function() {
    dashboardLog('Dashboard global bileşenleri Alpine.js\'e kaydedildi.');
  });
}