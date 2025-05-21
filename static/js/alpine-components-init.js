/**
 * Alpine.js Bileşenleri ve Store'ları için Merkezi Başlatma Dosyası
 * 
 * Bu dosya, VivaCRM projesinde Alpine.js bileşenlerinin ve store'larının
 * merkezi bir noktadan doğru sırayla başlatılmasını sağlar.
 */

// Alpine.js store'larını ve bileşenlerini başlat
window.AlpineInitialized = false;

// Sayfa yükleme ve HTMX swap olaylarını dinleyelim
document.addEventListener('DOMContentLoaded', initializeAlpine);
document.body.addEventListener('htmx:afterSwap', function(event) {
  if (typeof Alpine !== 'undefined' && typeof Alpine.initTree === 'function') {
    Alpine.initTree(event.detail.target);
  }
});

function initializeAlpine() {
  // Alpine.js'in yüklü olup olmadığını kontrol et
  if (!window.Alpine) {
    console.error('Alpine.js yüklü değil');
    return;
  }
  
  // Daha önce başlatılmış mı kontrol et
  if (window.AlpineInitialized) {
    console.log('Alpine.js daha önce başlatılmış, atlanıyor.');
    return;
  }

  // Tema Store'u ve Formatları Kaydet
  registerThemeStore();
  registerFormatters();

  // Özel Bileşenleri Kaydet
  registerOtherComponents();

  // Alpine.js'i henüz başlatılmamışsa başlat
  startAlpine();
}

/**
 * Alpine.js tema store'unu register et
 * Standardize edilmiş ThemeManager ile entegre çalışır
 */
function registerThemeStore() {
  // Eğer tema store'u zaten tanımlıysa, tekrar oluşturma
  if (Alpine.store('theme')) {
    console.log('Theme store zaten tanımlı, tekrar oluşturulmuyor');
    return;
  }
  
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
  
  // ThemeManager'ı yükleme fonksiyonu (gerekirse)
  const loadThemeManager = async () => {
    return new Promise((resolve) => {
      // Önce mevcut bir ThemeManager var mı kontrol et
      const existingManager = getStandardThemeManager();
      if (existingManager) {
        resolve(existingManager);
        return;
      }
      
      try {
        // ThemeManager script'ini dinamik olarak yükle
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
      } catch (error) {
        console.error('ThemeManager yükleme hatası:', error);
        resolve(null);
      }
    });
  };
  
  // ThemeManager'ı al
  const themeManager = getStandardThemeManager();
  
  // Alpine.js theme store tanımını oluştur
  try {
    if (themeManager) {
      // Standardize edilmiş ThemeManager ile entegre çalışan store tanımı
      Alpine.store('theme', {
        darkMode: themeManager.currentTheme === 'dark',
        systemPreference: themeManager.systemPreference,
        
        init() {
          // ThemeManager değişikliklerini dinle
          themeManager.subscribe((theme) => {
            this.darkMode = theme === 'dark';
          });
          
          console.log('Theme store ThemeManager ile başlatıldı, darkMode:', this.darkMode);
        },
        
        toggle() {
          themeManager.toggleTheme();
        },
        
        useSystemPreference() {
          themeManager.useSystemPreference();
        },
        
        applyTheme(theme) {
          themeManager.setTheme(theme);
        }
      });
    } else {
      console.warn('ThemeManager bulunamadı, alternatif yöntem deneniyor...');
      
      // ThemeManager yüklenene kadar bekleyecek geçici store
      Alpine.store('theme', {
        darkMode: localStorage.getItem('vivacrm-theme') === 'dark',
        systemPreference: window.matchMedia('(prefers-color-scheme: dark)').matches,
        
        async init() {
          // ThemeManager'ı dinamik olarak yüklemeyi dene
          const manager = await loadThemeManager();
          
          if (manager) {
            // ThemeManager başarıyla yüklendi, artık kullanabiliriz
            this.darkMode = manager.currentTheme === 'dark';
            this.systemPreference = manager.systemPreference;
            
            // ThemeManager değişikliklerini dinle
            manager.subscribe((theme) => {
              this.darkMode = theme === 'dark';
            });
            
            console.log('Theme store gecikmiş ThemeManager ile başlatıldı, darkMode:', this.darkMode);
            return;
          }
          
          // ThemeManager yüklenemedi, fallback davranış kullan
          console.warn('ThemeManager yüklenemedi, fallback davranış kullanılıyor');
          
          // Tema başlatma
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
        },
        
        toggle() {
          // ThemeManager'ı tekrar kontrol et (sonradan yüklenmiş olabilir)
          const manager = getStandardThemeManager();
          if (manager) {
            manager.toggleTheme();
            return;
          }
          
          // Fallback davranış
          this.darkMode = !this.darkMode;
          localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
          localStorage.setItem('vivacrm-theme-source', 'user');
          this.applyTheme(this.darkMode ? 'dark' : 'light');
          
          // Custom event yayınla
          document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', { 
            detail: { 
              theme: this.darkMode ? 'dark' : 'light', 
              darkMode: this.darkMode,
              source: 'alpine-components'
            } 
          }));
        },
        
        useSystemPreference() {
          // ThemeManager'ı tekrar kontrol et (sonradan yüklenmiş olabilir)
          const manager = getStandardThemeManager();
          if (manager) {
            manager.useSystemPreference();
            return;
          }
          
          // Fallback davranış
          this.darkMode = this.systemPreference;
          localStorage.setItem('vivacrm-theme-source', 'system');
          localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
          this.applyTheme(this.darkMode ? 'dark' : 'light');
        },
        
        applyTheme(theme) {
          // ThemeManager'ı tekrar kontrol et (sonradan yüklenmiş olabilir)
          const manager = getStandardThemeManager();
          if (manager) {
            manager.setTheme(theme);
            return;
          }
          
          // Fallback davranış
          // Tema dönüşümü
          const daisyUITheme = theme === 'dark' ? 'vivacrmDark' : 'vivacrm';
          
          // Tema uygula
          document.documentElement.setAttribute('data-theme', daisyUITheme);
          document.documentElement.classList.toggle('dark', theme === 'dark');
          
          // Temayı kaydet
          localStorage.setItem('vivacrm-theme', theme);
          
          // Tema değişikliği bildir
          document.dispatchEvent(new CustomEvent('vivacrm:theme-changed', {
            detail: { 
              theme: theme, 
              darkMode: theme === 'dark',
              source: 'alpine-components'
            }
          }));
        }
      });
    }
    
    // Theme store'u başlat
    if (typeof Alpine.store('theme').init === 'function') {
      Alpine.store('theme').init();
    }
    
    // Global erişim için window objesine de ekle
    window.themeStore = Alpine.store('theme');
    
  } catch (error) {
    console.error('Theme store başlatma hatası:', error);
  }
}

/**
 * Formatters yardımcı fonksiyonlarını magic helper olarak kaydet
 */
function registerFormatters() {
  // Önce global formatlama fonksiyonlarını oluştur
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
  
  window.formatCurrency = function(amount) {
    if (amount === null || amount === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };
  
  window.formatNumber = function(number, decimals = 0) {
    if (number === null || number === undefined) return '';
    
    return new Intl.NumberFormat('tr-TR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(number);
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
  
  // Formatters nesnesini de oluştur (geriye dönük uyumluluk için)
  window.formatters = {
    formatDate: window.formatDate,
    formatCurrency: window.formatCurrency,
    formatNumber: window.formatNumber,
    formatPercent: window.formatPercent
  };
  
  // Tarih formatlama magic helper
  if (typeof Alpine.magic === 'function') {
    Alpine.magic('formatDate', () => window.formatDate);
    Alpine.magic('formatCurrency', () => window.formatCurrency);
    Alpine.magic('formatNumber', () => window.formatNumber);
    Alpine.magic('formatPercent', () => window.formatPercent);
  }
  
  console.log('Format fonksiyonları başarıyla kaydedildi.');
}

/**
 * Dashboard bileşenlerini kaydet
 */
function registerDashboardComponents() {
  try {
    // Dashboard komponentlerini oluşturan modülü import et
    if (typeof dashboardComponent === 'function') {
      Alpine.data('dashboardComponent', dashboardComponent);
    }
    
    if (typeof dateFilterComponent === 'function') {
      Alpine.data('dateFilterComponent', dateFilterComponent);
    }
    
    if (typeof ordersTableApp === 'function') {
      Alpine.data('ordersTableApp', ordersTableApp);
    }
  } catch (error) {
    console.warn('Dashboard components not available:', error);
  }
}

/**
 * Diğer Alpine.js bileşenlerini kaydet
 */
function registerOtherComponents() {
  try {
    // Kullanılan bileşenleri kontrol et ve varsa register et
    
    // Modal ve Card bileşenlerini import et ve kaydet
    try {
      // ES Module'lerden import et (mevcut modüller)
      import('/static/js/alpine/components/modal.js')
        .then(module => {
          Alpine.data('modal', module.default);
          console.log('Modal bileşeni kaydedildi');
        })
        .catch(error => {
          console.error('Modal bileşeni yüklenemedi:', error);
        });

      import('/static/js/alpine/components/card.js')
        .then(module => {
          Alpine.data('card', module.default);
          console.log('Card bileşeni kaydedildi');
        })
        .catch(error => {
          console.error('Card bileşeni yüklenemedi:', error);
        });
    } catch (error) {
      console.warn('ES Module kullanılamadı, global bileşenlere geçiliyor');
      
      // Global nesneden erişmeyi dene
      if (window.modal) {
        Alpine.data('modal', window.modal);
      }
      
      if (window.card) {
        Alpine.data('card', window.card);
      }
    }
    
    // Dashboard bileşenlerini kaydet (global nesneden)
    if (window.dashboardComponent) {
      Alpine.data('dashboardComponent', window.dashboardComponent);
      console.log('Dashboard bileşeni kaydedildi');
    }
    
    if (window.dateFilterComponent) {
      Alpine.data('dateFilterComponent', window.dateFilterComponent);
      console.log('Date filter bileşeni kaydedildi');
    }
    
    if (window.ordersTableApp) {
      Alpine.data('ordersTableApp', window.ordersTableApp);
      console.log('Orders table bileşeni kaydedildi');
    }
    
  } catch (error) {
    console.warn('Bazı bileşenler kaydedilemedi:', error);
  }
}

/**
 * Alpine.js'i bir kez başlat
 */
function startAlpine() {
  // Alpine.js henüz başlatılmamışsa başlat
  if (!window.AlpineInitialized && typeof Alpine.start === 'function') {
    try {
      Alpine.start();
      window.AlpineInitialized = true;
      console.log('Alpine.js başarıyla başlatıldı');
    } catch (error) {
      console.error('Alpine.js başlatma hatası:', error);
    }
  }
}