/**
 * Inline Dashboard Components
 * 
 * Provides all dashboard functionality directly without requiring module imports.
 * Includes all formatters, dashboard components, and initialization.
 */

// Set up global namespace
window.VivaCRM = window.VivaCRM || {};

// ---- Format Helpers ----
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

// ---- Dashboard Theme Store ----
if (!window.Alpine.store || !window.Alpine.store('theme')) {
  // Standardize edilmiş ThemeManager'ı yükle ve kullan
  const getStandardThemeManager = () => {
    // Öncelikle window.VivaCRM.themeManager'ı kontrol et (doğru yazım)
    if (window.VivaCRM && window.VivaCRM.themeManager) {
      return window.VivaCRM.themeManager;
    }
    
    // Fallback olarak window.vivaCRM.themeManager'ı da kontrol et (eski yazım)
    if (window.vivaCRM && window.vivaCRM.themeManager) {
      return window.vivaCRM.themeManager;
    }
    
    // ThemeManager bulunamadı
    console.warn('Standardized ThemeManager not found, will attempt to load it');
    return null;
  };
  
  // Alpine theme store tanımı - her zaman ThemeManager'ı kullanacak şekilde
  window.Alpine.store('theme', {
    darkMode: false,
    systemPreference: window.matchMedia('(prefers-color-scheme: dark)').matches,
    
    init() {
      console.log('Initializing Alpine theme store with standardized ThemeManager');
      
      // ThemeManager'ı al
      const themeManager = getStandardThemeManager();
      
      if (themeManager) {
        // ThemeManager ile başlat
        this.darkMode = themeManager.currentTheme === 'dark';
        this.systemPreference = themeManager.systemPreference;
        
        // ThemeManager değişikliklerini dinle
        themeManager.subscribe((theme) => {
          this.darkMode = theme === 'dark';
        });
        
        console.log('Alpine theme store initialized with standardized ThemeManager');
      } else {
        // ThemeManager yoksa dinamik olarak yüklemeye çalış ve sonra tekrar dene
        console.warn('Loading ThemeManager dynamically');
        
        const script = document.createElement('script');
        script.src = '/static/js/theme-manager-standardized.js';
        script.onload = () => {
          // Script yüklendikten sonra tekrar ThemeManager'ı almaya çalış
          const loadedThemeManager = getStandardThemeManager();
          
          if (loadedThemeManager) {
            // ThemeManager bulundu, store'u güncelle
            this.darkMode = loadedThemeManager.currentTheme === 'dark';
            this.systemPreference = loadedThemeManager.systemPreference;
            
            // ThemeManager değişikliklerini dinle
            loadedThemeManager.subscribe((theme) => {
              this.darkMode = theme === 'dark';
            });
            
            console.log('Alpine theme store initialized with dynamically loaded ThemeManager');
          } else {
            console.error('Failed to load ThemeManager, using system defaults');
            // Fallback to system preference
            this.darkMode = this.systemPreference;
          }
        };
        
        document.head.appendChild(script);
      }
    },
    
    toggle() {
      // Her zaman standardize edilmiş ThemeManager'ı kullan
      const themeManager = getStandardThemeManager();
      
      if (themeManager) {
        themeManager.toggleTheme();
      } else {
        console.error('ThemeManager not available for toggle operation');
      }
    },
    
    useSystemPreference() {
      // Her zaman standardize edilmiş ThemeManager'ı kullan
      const themeManager = getStandardThemeManager();
      
      if (themeManager) {
        themeManager.useSystemPreference();
      } else {
        console.error('ThemeManager not available for system preference operation');
      }
    }
    
    // applyTheme metodu kaldırıldı çünkü artık her zaman ThemeManager kullanıyoruz
  });
}

// ---- Dashboard Components ----
// Main Dashboard Component
window.dashboardComponent = function() {
  return {
    // State variables
    loading: false,
    currentPeriod: 'month',
    customStartDate: null,
    customEndDate: null,
    charts: {},
    
    // Lifecycle methods
    initialize() {
      // Use server-sent initial data or fallback to window
      const initData = (window.VivaCRM && window.VivaCRM.dashboardInitData) || window.dashboardInitData;
      
      if (initData) {
        this.currentPeriod = initData.currentPeriod || 'month';
        this.customStartDate = initData.customStartDate || null;
        this.customEndDate = initData.customEndDate || null;
        console.log('Dashboard initialized with period:', this.currentPeriod);
      } else {
        console.warn('No dashboard init data found, using defaults');
      }
      
      // Set up event listeners
      this.setupEventListeners();
      
      // Initialize charts when DOM is ready
      this.$nextTick(() => {
        this.initializeCharts();
      });
    },
    
    // Set up HTMX event listeners
    setupEventListeners() {
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
      
      // Listen for theme changes
      window.addEventListener('theme-changed', () => {
        this.updateChartsTheme();
      });
    },
    
    // Change the selected period and refresh data
    setPeriod(period) {
      this.currentPeriod = period;
      this.refreshData();
    },
    
    // Refresh dashboard data
    refreshData() {
      this.loading = true;
      
      // Use HTMX to refresh dashboard content
      const dashboardContent = document.getElementById('dashboard-content');
      if (dashboardContent && window.htmx) {
        const periodParams = {
          period: this.currentPeriod
        };
        
        // Add custom date range parameters if needed
        if (this.currentPeriod === 'custom' && this.customStartDate && this.customEndDate) {
          periodParams.start_date = this.customStartDate;
          periodParams.end_date = this.customEndDate;
        }
        
        // Trigger HTMX request
        window.htmx.trigger(dashboardContent, 'periodChanged', {
          params: periodParams
        });
      }
    },
    
    // Apply custom date range
    applyCustomDateRange() {
      if (this.customStartDate && this.customEndDate) {
        this.currentPeriod = 'custom';
        this.refreshData();
      }
    },
    
    // Initialize charts
    initializeCharts() {
      if (typeof ApexCharts === 'undefined') {
        console.warn('ApexCharts not loaded, attempting to load from CDN');
        this.loadApexChartsFromCDN();
        return;
      }
      
      console.log('Initializing dashboard charts');
      
      // Get chart elements
      const chartElements = {
        sales: document.getElementById('salesChart'),
        categories: document.getElementById('categoryChart'),
        orders: document.getElementById('ordersChart')
      };
      
      // Create charts
      Object.entries(chartElements).forEach(([name, element]) => {
        if (!element) return;
        
        // Get chart options
        const options = this.getChartOptions(name);
        
        // Destroy existing chart
        if (this.charts[name]) {
          this.charts[name].destroy();
        }
        
        // Create new chart
        try {
          this.charts[name] = new ApexCharts(element, options);
          this.charts[name].render();
        } catch (error) {
          console.error(`Error creating ${name} chart:`, error);
        }
      });
      
      // Apply theme to charts
      this.updateChartsTheme();
    },
    
    // Load ApexCharts from CDN if needed
    loadApexChartsFromCDN() {
      if (document.querySelector('script[src*="apexcharts"]')) {
        return; // Already loading
      }
      
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/apexcharts';
      script.async = true;
      script.onload = () => {
        this.initializeCharts();
      };
      document.head.appendChild(script);
    },
    
    // Get chart options based on chart type
    getChartOptions(chartName) {
      // Use ThemeManager to check if dark mode is active
      const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
      const isDarkMode = themeManager ? 
        themeManager.currentTheme === 'dark' : 
        (document.documentElement.classList.contains('dark') || 
         document.documentElement.getAttribute('data-theme') === 'vivacrmDark');
      
      // Common chart options
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
                return window.formatCurrency(value);
              }
              return window.formatNumber(value);
            }
          }
        },
        grid: {
          borderColor: isDarkMode ? '#333' : '#e2e8f0',
          strokeDashArray: 3,
          position: 'back'
        }
      };
      
      // Chart-specific options
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
                      return window.formatNumber(val);
                    }
                  },
                  total: {
                    show: true,
                    showAlways: false,
                    label: 'Toplam',
                    formatter: function(w) {
                      const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                      return window.formatNumber(total);
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
    
    // Get chart data from HTML data attributes
    getChartData(chartName) {
      // Create element ID and get data from dataset
      const chartEl = document.getElementById(`${chartName}Chart`);
      if (chartEl && chartEl.dataset.series) {
        try {
          return JSON.parse(chartEl.dataset.series);
        } catch (e) {
          console.error(`Error parsing ${chartName} chart data:`, e);
        }
      }
      
      // Fallback data
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
    
    // Get chart categories from HTML data attributes
    getChartCategories(chartName) {
      // Create element ID and get data from dataset
      const chartEl = document.getElementById(`${chartName}Chart`);
      if (chartEl && chartEl.dataset.categories) {
        try {
          return JSON.parse(chartEl.dataset.categories);
        } catch (e) {
          console.error(`Error parsing ${chartName} chart categories:`, e);
        }
      }
      
      // Fallback categories
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
    
    // Update chart themes
    updateChartsTheme() {
      // Use ThemeManager to check if dark mode is active
      const themeManager = window.VivaCRM && window.VivaCRM.themeManager;
      const isDarkMode = themeManager ? 
        themeManager.currentTheme === 'dark' : 
        (document.documentElement.classList.contains('dark') || 
         document.documentElement.getAttribute('data-theme') === 'vivacrmDark');
      
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
    }
  };
};

// Date Filter Component
window.dateFilterComponent = function() {
  return {
    // State variables
    showDatePicker: false,
    startDate: null,
    endDate: null,
    
    // Lifecycle method
    init() {
      // Get date values from parent dashboard component
      if (this.$root.customStartDate) {
        this.startDate = this.$root.customStartDate;
      }
      
      if (this.$root.customEndDate) {
        this.endDate = this.$root.customEndDate;
      }
    },
    
    // Toggle date picker visibility
    toggleDatePicker() {
      this.showDatePicker = !this.showDatePicker;
    },
    
    // Apply custom date range
    applyCustomDateRange() {
      if (!this.startDate || !this.endDate) {
        alert('Lütfen başlangıç ve bitiş tarihlerini seçin');
        return;
      }
      
      // Validate dates
      const startDate = new Date(this.startDate);
      const endDate = new Date(this.endDate);
      
      if (startDate > endDate) {
        alert('Başlangıç tarihi bitiş tarihinden sonra olamaz');
        return;
      }
      
      // Apply to parent component
      this.$root.customStartDate = this.startDate;
      this.$root.customEndDate = this.endDate;
      this.$root.setPeriod('custom');
      
      // Close date picker
      this.showDatePicker = false;
    },
    
    // Preset for last month
    setLastMonth() {
      const today = new Date();
      const lastMonth = new Date(today);
      lastMonth.setMonth(today.getMonth() - 1);
      
      this.startDate = this.formatDateForInput(lastMonth);
      this.endDate = this.formatDateForInput(today);
      
      this.applyCustomDateRange();
    },
    
    // Preset for last quarter
    setLastQuarter() {
      const today = new Date();
      const lastQuarter = new Date(today);
      lastQuarter.setMonth(today.getMonth() - 3);
      
      this.startDate = this.formatDateForInput(lastQuarter);
      this.endDate = this.formatDateForInput(today);
      
      this.applyCustomDateRange();
    },
    
    // Format date for input (YYYY-MM-DD)
    formatDateForInput(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      
      return `${year}-${month}-${day}`;
    }
  };
};

// Initialize Alpine if it exists but hasn't been started yet
if (window.Alpine && !window.VivaCRM.alpineInitialized) {
  // Start Alpine.js (if not already started)
  if (typeof window.Alpine.start === 'function') {
    window.Alpine.start();
    window.VivaCRM.alpineInitialized = true;
    console.log('Alpine.js initialized by dashboard-components-inline.js');
  }
}

console.log('Dashboard components loaded and available globally');

// If we're using Alpine.data, register components
if (window.Alpine && typeof window.Alpine.data === 'function') {
  window.Alpine.data('dashboardComponent', window.dashboardComponent);
  window.Alpine.data('dateFilterComponent', window.dateFilterComponent);
  
  console.log('Dashboard components registered with Alpine.data()');
  
  // Make sure theme store is initialized
  if (window.Alpine.store && window.Alpine.store('theme')) {
    try {
      window.Alpine.store('theme').init();
      console.log('Theme store initialized');
    } catch (e) {
      console.error('Error initializing theme store:', e);
    }
  }
}