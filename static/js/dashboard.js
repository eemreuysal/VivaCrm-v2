/**
 * Dashboard Component Scripts
 * VivaCRM Dashboard için Alpine.js komponentlerini tanımlar
 */

// Theme Store - Standardize edilmiş ThemeManager ile entegre
if (!window.Alpine?.store('theme')) {
  document.addEventListener('DOMContentLoaded', function() {
    if (window.Alpine) {
      // ThemeManager'a erişim fonksiyonu
      const getStandardThemeManager = () => {
        // İlk olarak VivaCRM.themeManager'ı kontrol et (tercih edilen)
        if (window.VivaCRM && window.VivaCRM.themeManager) {
          return window.VivaCRM.themeManager;
        }
        
        // Geriye dönük uyumluluk için vivaCRM.themeManager'ı da kontrol et
        if (window.vivaCRM && window.vivaCRM.themeManager) {
          return window.vivaCRM.themeManager;
        }
        
        return null;
      };
      
      // ThemeManager'ı yükleme fonksiyonu
      const loadThemeManager = async () => {
        return new Promise((resolve) => {
          // Önce mevcut bir ThemeManager var mı kontrol et
          const existingManager = getStandardThemeManager();
          if (existingManager) {
            resolve(existingManager);
            return;
          }
          
          // ThemeManager'ı dinamik olarak yükle
          const script = document.createElement('script');
          script.src = '/static/js/theme-manager-standardized.js';
          script.type = 'module';
          
          script.onload = () => {
            // Yüklendikten sonra biraz bekle ve tekrar kontrol et
            setTimeout(() => {
              const manager = getStandardThemeManager();
              resolve(manager);
            }, 300);
          };
          
          script.onerror = () => {
            console.error('ThemeManager yüklenemedi.');
            resolve(null);
          };
          
          document.head.appendChild(script);
        });
      };
      
      // Alpine.js theme store'u
      Alpine.store('theme', {
        darkMode: false,
        systemPreference: window.matchMedia('(prefers-color-scheme: dark)').matches,
        
        async init() {
          // ThemeManager'a eriş veya yükle
          const themeManager = getStandardThemeManager() || await loadThemeManager();
          
          if (themeManager) {
            // ThemeManager ile entegre çalış
            this.darkMode = themeManager.currentTheme === 'dark';
            this.systemPreference = themeManager.systemPreference;
            
            // ThemeManager değişikliklerini dinle
            themeManager.subscribe((theme) => {
              this.darkMode = theme === 'dark';
            });
            
            console.log('Dashboard: Theme store ThemeManager ile entegre çalışıyor');
          } else {
            // Fallback davranış
            console.warn('Dashboard: ThemeManager bulunamadı, fallback davranış kullanılıyor');
            
            // Temel durumu ayarla
            this.darkMode = localStorage.getItem('vivacrm-theme') === 'dark';
            
            // Sistem tercihini izle
            window.matchMedia('(prefers-color-scheme: dark)')
              .addEventListener('change', e => {
                this.systemPreference = e.matches;
                if (localStorage.getItem('vivacrm-theme-source') === 'system') {
                  this.applyTheme(e.matches ? 'dark' : 'light');
                }
              });
            
            // Tema değişikliklerini dinle
            document.addEventListener('vivacrm:theme-changed', (e) => {
              if (e.detail) {
                if (typeof e.detail.theme === 'string') {
                  this.darkMode = e.detail.theme === 'dark';
                } else if (typeof e.detail.darkMode === 'boolean') {
                  this.darkMode = e.detail.darkMode;
                }
              }
            });
            
            // Kaydedilmiş tema veya sistem tercihi
            const savedTheme = localStorage.getItem('vivacrm-theme');
            const savedSource = localStorage.getItem('vivacrm-theme-source');
            
            if (savedTheme) {
              this.applyTheme(savedTheme);
            } else if (savedSource === 'system' || !savedSource) {
              this.useSystemPreference();
            } else {
              this.applyTheme('light'); // Varsayılan
            }
          }
        },
        
        toggle() {
          const themeManager = getStandardThemeManager();
          
          if (themeManager) {
            themeManager.toggleTheme();
            return;
          }
          
          // Fallback davranış
          const newTheme = this.darkMode ? 'light' : 'dark';
          this.applyTheme(newTheme);
          localStorage.setItem('vivacrm-theme-source', 'user');
          
          // Event gönder
          document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', {
            detail: { theme: newTheme, darkMode: newTheme === 'dark', source: 'alpine-dashboard' }
          }));
        },
        
        useSystemPreference() {
          const themeManager = getStandardThemeManager();
          
          if (themeManager) {
            themeManager.useSystemPreference();
            return;
          }
          
          // Fallback davranış
          const theme = this.systemPreference ? 'dark' : 'light';
          this.applyTheme(theme);
          localStorage.setItem('vivacrm-theme-source', 'system');
          
          // Event gönder
          document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', {
            detail: { theme: theme, darkMode: theme === 'dark', source: 'alpine-dashboard' }
          }));
        },
        
        applyTheme(theme) {
          const themeManager = getStandardThemeManager();
          
          if (themeManager) {
            themeManager.setTheme(theme);
            return;
          }
          
          // Fallback davranış
          if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'vivacrmDark');
            document.documentElement.classList.add('dark');
            this.darkMode = true;
          } else {
            document.documentElement.setAttribute('data-theme', 'vivacrm');
            document.documentElement.classList.remove('dark');
            this.darkMode = false;
          }
          
          localStorage.setItem('vivacrm-theme', theme);
        }
      });
      
      // Theme store'u başlat
      if (Alpine.store('theme') && typeof Alpine.store('theme').init === 'function') {
        Alpine.store('theme').init();
      }
    }
  });
}

// Dashboard Component
window.dashboardComponent = function() {
  return {
    loading: true,
    currentPeriod: window.dashboardInitData?.currentPeriod || 'month',
    customStartDate: window.dashboardInitData?.customStartDate || '',
    customEndDate: window.dashboardInitData?.customEndDate || '',
    
    init() {
      // Loading durumunu kapat
      setTimeout(() => {
        this.loading = false;
      }, 500);
    },
    
    setPeriod(period) {
      this.currentPeriod = period;
      this.refreshDashboard();
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    },
    
    refreshDashboard() {
      const url = new URL(window.location);
      url.searchParams.set('period', this.currentPeriod);
      
      if (this.currentPeriod === 'custom') {
        if (this.customStartDate) url.searchParams.set('start_date', this.customStartDate);
        if (this.customEndDate) url.searchParams.set('end_date', this.customEndDate);
      } else {
        url.searchParams.delete('start_date');
        url.searchParams.delete('end_date');
      }
      
      // Sayfayı yenile
      window.location.href = url.toString();
    }
  };
};

// Date Filter Component
window.dateFilterComponent = function() {
  return {
    showDatePicker: false,
    customStartDate: window.dashboardInitData?.customStartDate || '',
    customEndDate: window.dashboardInitData?.customEndDate || '',
    
    toggleDatePicker() {
      this.showDatePicker = !this.showDatePicker;
    },
    
    applyCustomDateRange() {
      if (this.customStartDate && this.customEndDate) {
        this.$parent.currentPeriod = 'custom';
        this.$parent.customStartDate = this.customStartDate;
        this.$parent.customEndDate = this.customEndDate;
        this.$parent.refreshDashboard();
      }
      this.showDatePicker = false;
    }
  };
};

// Recent Orders Table Component
window.ordersTableApp = function() {
  return {
    expandedOrderId: null,
    
    toggleOrderDetails(orderId) {
      this.expandedOrderId = this.expandedOrderId === orderId ? null : orderId;
    },
    
    isExpanded(orderId) {
      return this.expandedOrderId === orderId;
    }
  };
};

// Low Stock Products Component
window.lowStockApp = function() {
  return {
    showAll: false,
    
    toggleShowAll() {
      this.showAll = !this.showAll;
    }
  };
};

// Charts initialization via ApexCharts will be handled via the included script in the charts partial