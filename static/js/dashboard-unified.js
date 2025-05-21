/**
 * VivaCRM Dashboard Unified JS
 * 
 * Bu dosya, dashboard için tüm JavaScript işlevlerini tek bir modülde birleştirir.
 * Bileşenler, HTMX entegrasyonu ve grafik yönetimini optimize eder.
 */

// Alpine.js bileşenleri ve yardımcı fonksiyonları içe aktar
import { dashboardComponent, dateFilterComponent, ordersTableApp } from './components/dashboard-components.js';

// Dışa aktarılan bileşenler (diğer modüller tarafından kullanılabilir)
export { dashboardComponent, dateFilterComponent, ordersTableApp };

// DOM hazır olduğunda çalışacak kod
document.addEventListener('DOMContentLoaded', () => {
    console.log('VivaCRM Dashboard Unified JS initializing...');
    
    // Alpine.js bileşenlerini kaydet (Alpine.js yüklenmişse)
    if (window.Alpine) {
        registerAlpineComponents();
        setupEventHandlers();
        initializeChartSystem();
    } else {
        console.error('Alpine.js not loaded, dashboard functionality will be limited');
    }
});

/**
 * Alpine.js bileşenlerini kaydeder
 */
function registerAlpineComponents() {
    // Ana dashboard bileşenlerini kaydet
    window.Alpine.data('dashboardComponent', dashboardComponent);
    window.Alpine.data('dateFilterComponent', dateFilterComponent);
    window.Alpine.data('ordersTableApp', ordersTableApp);
    
    // Global değişkenleri ayarla
    window.VivaCRM = window.VivaCRM || {};
    window.VivaCRM.dashboard = {
        refreshCharts: refreshAllCharts,
        updateTheme: updateChartsTheme
    };
    
    console.log('Alpine.js components registered successfully');
}

/**
 * Olay işleyicilerini yapılandırır
 */
function setupEventHandlers() {
    setupHtmxEvents();
    setupThemeEvents();
    setupCustomEvents();
}

/**
 * HTMX olay işleyicilerini yapılandırır
 */
function setupHtmxEvents() {
    // HTMX yüklenmişse olay işleyicileri kur
    if (window.htmx) {
        // Dashboard içeriği güncellendiğinde
        document.body.addEventListener('htmx:afterSwap', (event) => {
            if (event.detail.target.id === 'dashboard-content') {
                console.log('Dashboard content swapped, reinitializing components');
                
                // Alpine.js komponenti güncellemesi
                if (window.Alpine && window.Alpine.initTree) {
                    window.Alpine.initTree(event.detail.target);
                }
                
                // Grafik sistemi güncellemesi
                setTimeout(() => {
                    refreshAllCharts();
                }, 100);
                
                // Yükleme durumunu kapat
                const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
                if (dashboardEl && dashboardEl.__x) {
                    dashboardEl.__x.$data.loading = false;
                }
            }
        });
        
        // İstek başlamadan önce
        document.body.addEventListener('htmx:beforeRequest', (event) => {
            if (event.detail.target.id === 'dashboard-content') {
                // Yükleme durumunu göster
                const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
                if (dashboardEl && dashboardEl.__x) {
                    dashboardEl.__x.$data.loading = true;
                }
            }
        });
        
        // Period değiştiğinde
        document.body.addEventListener('periodChanged', (event) => {
            handlePeriodChange(event);
        });
        
        console.log('HTMX events registered successfully');
    }
}

/**
 * Dönem değişikliğini ele alır
 * @param {Event} event Özel olay
 */
function handlePeriodChange(event) {
    // Alpine.js dashboard bileşeninden değerleri al
    const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
    if (!dashboardEl || !dashboardEl.__x) return;
    
    const component = dashboardEl.__x.$data;
    const dashboardContent = document.getElementById('dashboard-content');
    
    if (dashboardContent && window.htmx) {
        // HTMX değerlerini ayarla
        const params = new URLSearchParams();
        params.set('period', component.currentPeriod);
        
        // Özel tarih aralığı için parametreler ekle
        if (component.currentPeriod === 'custom' && component.customStartDate && component.customEndDate) {
            params.set('start_date', component.customStartDate);
            params.set('end_date', component.customEndDate);
        }
        
        // URL'i güncelle
        const newUrl = new URL(window.location.href);
        newUrl.search = params.toString();
        window.history.pushState({}, '', newUrl.toString());
        
        // HTMX yükleme tetikleyicisi
        htmx.trigger(dashboardContent, 'load');
    }
}

/**
 * Tema değişikliği olaylarını yapılandırır
 */
function setupThemeEvents() {
    // Tema değişikliği olayını dinle
    window.addEventListener('theme-changed', () => {
        console.log('Theme changed, updating dashboard charts');
        updateChartsTheme();
    });
}

/**
 * Özel olayları yapılandırır
 */
function setupCustomEvents() {
    // Özel olayları dinle (örn. grafikler hazır olduğunda)
    document.addEventListener('chartsReady', () => {
        console.log('Charts ready event detected');
        refreshAllCharts();
    });
    
    // Sayfa boyutu değiştiğinde grafikleri yeniden boyutlandır
    window.addEventListener('resize', debounce(() => {
        if (window.VivaCRM && window.VivaCRM.dashboard) {
            window.VivaCRM.dashboard.refreshCharts();
        }
    }, 250));
}

/**
 * Grafik sistemini başlatır
 */
function initializeChartSystem() {
    // ApexCharts kontrolü
    if (typeof ApexCharts === 'undefined') {
        loadApexChartsLibrary();
    } else {
        console.log('ApexCharts already loaded');
        // İlk grafik yenileme
        setTimeout(() => {
            refreshAllCharts();
        }, 300);
    }
}

/**
 * ApexCharts kütüphanesini dinamik olarak yükler
 */
function loadApexChartsLibrary() {
    console.log('Loading ApexCharts from CDN');
    
    // Zaten yükleniyor mu kontrol et
    if (document.querySelector('script[src*="apexcharts"]')) {
        return;
    }
    
    // Yeni script elementi oluştur ve ekle
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/apexcharts';
    script.async = true;
    script.onload = () => {
        console.log('ApexCharts loaded successfully');
        
        // Grafikleri başlat
        setTimeout(() => {
            refreshAllCharts();
            // Özel olay tetikle
            document.dispatchEvent(new CustomEvent('chartsReady'));
        }, 300);
    };
    document.head.appendChild(script);
}

/**
 * Tüm grafikleri yeniden oluşturur
 */
function refreshAllCharts() {
    console.log('Refreshing all dashboard charts');
    
    const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
    if (dashboardEl && dashboardEl.__x && typeof ApexCharts !== 'undefined') {
        try {
            // Mevcut grafikleri temizle ve yeniden oluştur
            dashboardEl.__x.$data.initializeCharts();
            
            // Tema güncellemesi
            updateChartsTheme();
            
            console.log('Charts refreshed successfully');
        } catch (error) {
            console.error('Error refreshing charts:', error);
        }
    } else {
        console.warn('Cannot refresh charts: Dashboard component or ApexCharts not available');
    }
}

/**
 * Tüm grafiklerin temasını günceller
 */
function updateChartsTheme() {
    console.log('Updating chart themes');
    
    const isDarkMode = document.documentElement.classList.contains('dark') || 
                     document.documentElement.getAttribute('data-theme') === 'dark';
    
    const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
    if (dashboardEl && dashboardEl.__x) {
        const component = dashboardEl.__x.$data;
        
        if (component.charts && Object.keys(component.charts).length > 0) {
            // Her grafik için tema güncelle
            Object.values(component.charts).forEach((chart) => {
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
            console.log(`Charts updated to ${isDarkMode ? 'dark' : 'light'} theme`);
        }
    }
}

/**
 * Belirli bir fonksiyonu geciktiren debounce yardımcısı
 * @param {Function} func Çalıştırılacak fonksiyon
 * @param {number} delay Gecikme (ms)
 * @returns {Function} Debounce edilmiş fonksiyon
 */
function debounce(func, delay) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}