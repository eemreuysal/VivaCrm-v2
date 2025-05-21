/**
 * VivaCRM Dashboard Fix
 * 
 * Bu script, dashboard bileşenlerini düzeltir ve iyileştirmeler yapar:
 * 1. Alpine.js komponenti yükleme ve başlatma sorunlarını giderir
 * 2. HTMX entegrasyonunu iyileştirir ve döngüleri engeller
 * 3. Grafik yükleme ve render sorunlarını çözer
 * 4. Tema değişikliği için doğru olay yayınını sağlar
 */

document.addEventListener('DOMContentLoaded', function() {
    // Dashboard bileşenlerini yükle ve başlat
    initializeDashboard();
});

/**
 * Dashboard bileşenlerini ve eventlerini başlatır
 */
function initializeDashboard() {
    console.log('Dashboard fix script initializing...');
    
    // Alpine.js yüklenmiş mi kontrol et
    if (window.Alpine) {
        console.log('Alpine.js detected');
        
        // HTMX yüklenmiş mi kontrol et
        if (window.htmx) {
            console.log('HTMX detected');
            setupHtmxEvents();
        } else {
            console.error('HTMX not loaded, some dashboard features might not work correctly');
        }
        
        // Chart.js veya ApexCharts kurulumu kontrolü
        checkAndLoadChartLibrary();
        
        // Alpine.js store durumunu sıfırla
        resetAlpineState();
    } else {
        console.error('Alpine.js not loaded, dashboard will not function correctly');
    }
}

/**
 * HTMX olaylarını düzenler
 */
function setupHtmxEvents() {
    // HTMX olay işleyicilerini temizle ve yeniden ayarla
    document.body.removeEventListener('htmx:afterSwap', afterSwapHandler);
    document.body.removeEventListener('htmx:beforeRequest', beforeRequestHandler);
    document.body.removeEventListener('periodChanged', periodChangedHandler);
    
    // Yeni işleyicileri ekle
    document.body.addEventListener('htmx:afterSwap', afterSwapHandler);
    document.body.addEventListener('htmx:beforeRequest', beforeRequestHandler);
    document.body.addEventListener('periodChanged', periodChangedHandler);
    
    // URL/tarih parametreleri değişimiyle sayfa güncelleme sorunu çözümü
    window.addEventListener('popstate', function(event) {
        // URL değiştiğinde dashboard içeriğini yenile
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent && window.htmx) {
            window.htmx.trigger(dashboardContent, 'htmx:load');
        }
    });
}

/**
 * HTMX afterSwap olayı için işleyici
 */
function afterSwapHandler(event) {
    if (event.detail.target.id === 'dashboard-content') {
        console.log('Dashboard content updated');
        
        // Yükleme durumunu kapat
        const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
        if (dashboardEl && dashboardEl.__x) {
            dashboardEl.__x.$data.loading = false;
        }
        
        // Alpine bileşenlerini yeniden başlat
        if (window.Alpine && window.Alpine.initTree) {
            window.Alpine.initTree(event.detail.target);
        }
        
        // Grafikleri yeniden başlatır
        initializeCharts();
    }
}

/**
 * HTMX beforeRequest olayı için işleyici
 */
function beforeRequestHandler(event) {
    if (event.detail.target.id === 'dashboard-content') {
        console.log('Loading dashboard content...');
        
        // Yükleme durumunu göster
        const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
        if (dashboardEl && dashboardEl.__x) {
            dashboardEl.__x.$data.loading = true;
        }
    }
}

/**
 * HTMX periodChanged olayı için işleyici
 */
function periodChangedHandler(event) {
    // Ana dashboard komponentinden değerleri al
    const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
    if (dashboardEl && dashboardEl.__x) {
        const component = dashboardEl.__x.$data;
        
        // Dashboard içeriğini bul
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent && window.htmx) {
            // HTMX parametrelerini ayarla
            const params = new URLSearchParams();
            params.set('period', component.currentPeriod);
            
            // Özel tarih aralığı için parametreler ekle
            if (component.currentPeriod === 'custom' && component.customStartDate && component.customEndDate) {
                params.set('start_date', component.customStartDate);
                params.set('end_date', component.customEndDate);
            }
            
            // URL'i güncelle (pushState ile)
            const newUrl = new URL(window.location.href);
            newUrl.search = params.toString();
            window.history.pushState({}, '', newUrl.toString());
            
            // HTMX vals değerlerini güncelle ve yükleme tetikle
            htmx.trigger(dashboardContent, 'load');
        }
    }
}

/**
 * Grafik kütüphanesini kontrol eder ve gerekirse yükler
 */
function checkAndLoadChartLibrary() {
    if (typeof ApexCharts === 'undefined') {
        console.log('ApexCharts not loaded, attempting to load from CDN');
        
        // Script zaten eklenmiş mi kontrol et
        if (document.querySelector('script[src*="apexcharts"]')) {
            return; // Yükleme başlatılmış, bekle
        }
        
        // ApexCharts'ı CDN'den yükle
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/apexcharts';
        script.async = true;
        script.onload = function() {
            console.log('ApexCharts loaded successfully');
            initializeCharts();
        };
        document.head.appendChild(script);
    } else {
        console.log('ApexCharts already loaded');
    }
}

/**
 * Dashboard grafiklerini başlatır
 */
function initializeCharts() {
    console.log('Initializing charts...');
    
    // Grafik başlatması için dashboardComponent'a erişim
    const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
    if (dashboardEl && dashboardEl.__x && typeof ApexCharts !== 'undefined') {
        // Komponent metodunu çağır
        dashboardEl.__x.$data.initializeCharts();
        
        // Tema uygulamasını zorla
        dashboardEl.__x.$data.updateChartsTheme();
    } else {
        console.log('Dashboard component or ApexCharts not ready');
    }
}

/**
 * Alpine.js store durumunu sıfırlar
 */
function resetAlpineState() {
    // Alpine verilerini sıfırla
    if (window.Alpine && window.Alpine.store) {
        // Tema bilgisini al
        const darkMode = document.documentElement.classList.contains('dark') || 
                        document.documentElement.getAttribute('data-theme') === 'dark';
        
        // Window global durumunu kontrol et ve güncelle
        window.VivaCRM = window.VivaCRM || {};
        
        // Tema değişikliği için event listener ekle
        document.addEventListener('theme-changed', function() {
            console.log('Theme changed event detected');
            
            // Grafiklere tema değişikliğini bildir
            const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
            if (dashboardEl && dashboardEl.__x) {
                dashboardEl.__x.$data.updateChartsTheme();
            }
        });
    }
}

// Tema değişikliği olayını yakalama ve işleme
window.addEventListener('theme-changed', function() {
    console.log('Theme changed, updating dashboard...');
    
    // Tüm grafikleri tema değişimine göre güncelle
    const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
    if (dashboardEl && dashboardEl.__x) {
        console.log('Updating chart themes...');
        dashboardEl.__x.$data.updateChartsTheme();
    }
});

/**
 * Sayfa değişikliğinde Alpine.js ve grafikleri sıfırla
 */
window.addEventListener('turbolinks:load', function() {
    console.log('Page change detected, reinitializing dashboard');
    initializeDashboard();
});

// Periyodik yenileme için yardımcı fonksiyon
function setupDashboardAutoRefresh(intervalSeconds) {
    if (intervalSeconds && intervalSeconds > 0) {
        console.log(`Auto-refresh enabled: ${intervalSeconds} seconds`);
        
        // Varolan interval'ı temizle
        if (window.dashboardRefreshInterval) {
            clearInterval(window.dashboardRefreshInterval);
        }
        
        // Yeni interval kur
        window.dashboardRefreshInterval = setInterval(() => {
            const dashboardContent = document.getElementById('dashboard-content');
            if (dashboardContent && window.htmx) {
                window.htmx.trigger(dashboardContent, 'periodChanged');
            }
        }, intervalSeconds * 1000);
    }
}