/**
 * VivaCRM Chart System
 * 
 * Gelişmiş grafik render sistemi ve yönetimi.
 * Bu modül, grafiklerin oluşturulması, yenilenmesi ve
 * tema değişikliklerine otomatik uyum sağlaması için
 * merkezi bir alt yapı sağlar.
 */

// Grafik konfigürasyonları ve yardımcı fonksiyonları
const ChartSystem = (function() {
    // Private değişkenler
    let chartInstances = {};
    let isDarkMode = false;
    let isInitialized = false;
    
    // ApexCharts'ın yüklü olup olmadığını kontrol et
    function _ensureApexChartsLoaded() {
        return new Promise((resolve, reject) => {
            if (typeof ApexCharts !== 'undefined') {
                resolve();
                return;
            }
            
            console.log('Loading ApexCharts from CDN');
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/apexcharts';
            script.async = true;
            script.onload = resolve;
            script.onerror = () => reject(new Error('ApexCharts could not be loaded'));
            document.head.appendChild(script);
        });
    }
    
    // Şu anki tema modunu al
    function _detectThemeMode() {
        isDarkMode = document.documentElement.classList.contains('dark') || 
                    document.documentElement.getAttribute('data-theme') === 'dark';
        return isDarkMode;
    }
    
    // Mevcut grafikleri temizle
    function _destroyExistingCharts() {
        Object.values(chartInstances).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                try {
                    chart.destroy();
                } catch (error) {
                    console.error('Error destroying chart:', error);
                }
            }
        });
        chartInstances = {};
    }
    
    // Grafik elementinin verilerini parse et
    function _parseChartData(element) {
        const data = {
            categories: [],
            series: []
        };
        
        try {
            if (element.dataset.categories) {
                data.categories = JSON.parse(element.dataset.categories);
            }
            
            if (element.dataset.series) {
                data.series = JSON.parse(element.dataset.series);
            }
        } catch (error) {
            console.error('Error parsing chart data:', error);
        }
        
        return data;
    }
    
    // Ortak grafik ayarlarını al
    function _getCommonOptions() {
        const isDark = _detectThemeMode();
        
        return {
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
                mode: isDark ? 'dark' : 'light'
            },
            tooltip: {
                theme: isDark ? 'dark' : 'light'
            },
            grid: {
                borderColor: isDark ? '#333' : '#e2e8f0',
                strokeDashArray: 3,
                position: 'back'
            }
        };
    }
    
    // Grafik türüne göre özel ayarlar
    function _getChartOptions(chartType, data) {
        const commonOptions = _getCommonOptions();
        
        // Ticarileştirme için para birimi formatı
        const currencyFormatter = new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY'
        });
        
        // Standart sayı formatı
        const numberFormatter = new Intl.NumberFormat('tr-TR');
        
        // Grafik türüne göre özel ayarlar
        switch (chartType) {
            case 'sales':
                return {
                    ...commonOptions,
                    chart: {
                        ...commonOptions.chart,
                        type: 'area',
                        height: 350
                    },
                    series: Array.isArray(data.series) ? data.series : [{
                        name: 'Satışlar',
                        data: Array.isArray(data.series) ? data.series : [0, 0]
                    }],
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
                        categories: data.categories || [],
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
                    },
                    tooltip: {
                        ...commonOptions.tooltip,
                        y: {
                            formatter: (value) => currencyFormatter.format(value)
                        }
                    }
                };
                
            case 'category':
                return {
                    ...commonOptions,
                    chart: {
                        ...commonOptions.chart,
                        type: 'donut',
                        height: 350
                    },
                    series: data.series || [],
                    labels: data.categories || [],
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
                                            return numberFormatter.format(val);
                                        }
                                    },
                                    total: {
                                        show: true,
                                        showAlways: false,
                                        label: 'Toplam',
                                        formatter: function(w) {
                                            const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                            return numberFormatter.format(total);
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
            default:
                return {
                    ...commonOptions,
                    chart: {
                        ...commonOptions.chart,
                        type: 'bar',
                        height: 350
                    },
                    series: Array.isArray(data.series) ? data.series : [{
                        name: 'Siparişler',
                        data: Array.isArray(data.series) ? data.series : [0, 0]
                    }],
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
                        categories: data.categories || [],
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
                    },
                    tooltip: {
                        ...commonOptions.tooltip,
                        y: {
                            formatter: (value) => numberFormatter.format(value)
                        }
                    }
                };
        }
    }
    
    // Public API
    return {
        // Grafik sistemini başlat
        initialize: async function() {
            try {
                // ApexCharts'ın yüklü olduğundan emin ol
                await _ensureApexChartsLoaded();
                
                // Tema durumunu algıla
                _detectThemeMode();
                
                // Mevcut grafikleri temizle
                _destroyExistingCharts();
                
                // DOM'daki tüm grafik elementlerini bul ve render et
                this.refreshAllCharts();
                
                // Tema değişikliklerini dinle
                document.addEventListener('theme-changed', () => {
                    this.updateChartsTheme();
                });
                
                // Sayfa yeniden boyutlandırıldığında grafikleri güncelle
                window.addEventListener('resize', debounce(() => {
                    this.refreshAllCharts();
                }, 250));
                
                isInitialized = true;
                console.log('Chart System initialized successfully');
                
                // Başarıyla başlatıldı olayını tetikle
                document.dispatchEvent(new CustomEvent('charts-system-ready'));
                
            } catch (error) {
                console.error('Failed to initialize chart system:', error);
                throw error;
            }
        },
        
        // Grafik varsa al, yoksa oluştur
        getOrCreateChart: function(elementId, chartType) {
            // Element ID belirtilmişse ve DOM'da varsa
            const element = document.getElementById(elementId);
            if (!element) {
                console.error(`Chart element with ID "${elementId}" not found`);
                return null;
            }
            
            // Grafik tipi belirtilmemişse element'ten al
            if (!chartType) {
                chartType = element.dataset.chartType || 'default';
            }
            
            // Grafik zaten oluşturulmuşsa onu döndür
            if (chartInstances[elementId]) {
                return chartInstances[elementId];
            }
            
            try {
                // Grafik verilerini parse et
                const data = _parseChartData(element);
                
                // Grafik ayarlarını al
                const options = _getChartOptions(chartType, data);
                
                // Yeni grafik oluştur
                const chart = new ApexCharts(element, options);
                chart.render();
                
                // Referansı kaydet
                chartInstances[elementId] = chart;
                
                return chart;
            } catch (error) {
                console.error(`Error creating chart "${elementId}":`, error);
                return null;
            }
        },
        
        // Tüm grafikleri yeniden render et
        refreshAllCharts: function() {
            // Hazır değilse başlat
            if (!isInitialized) {
                this.initialize();
                return;
            }
            
            // Mevcut grafikleri temizle
            _destroyExistingCharts();
            
            // DOM'daki grafik elementlerini bul
            const chartElements = document.querySelectorAll('[data-chart-type]');
            
            // Her bir grafik için
            chartElements.forEach(element => {
                const chartId = element.id;
                const chartType = element.dataset.chartType;
                
                // Benzersiz ID'si yoksa atla
                if (!chartId) {
                    console.warn('Chart element without ID found. Skipping.');
                    return;
                }
                
                // Grafik oluştur
                this.getOrCreateChart(chartId, chartType);
            });
            
            console.log(`Refreshed ${chartElements.length} charts`);
        },
        
        // Tema değişikliğine göre grafikleri güncelle
        updateChartsTheme: function() {
            // Güncel tema modunu al
            const isDark = _detectThemeMode();
            
            // Tema güncellenecek ayarlar
            const themeOptions = {
                theme: {
                    mode: isDark ? 'dark' : 'light'
                },
                tooltip: {
                    theme: isDark ? 'dark' : 'light'
                },
                grid: {
                    borderColor: isDark ? '#333' : '#e2e8f0'
                }
            };
            
            // Tüm grafiklerin temasını güncelle
            Object.values(chartInstances).forEach(chart => {
                if (chart && typeof chart.updateOptions === 'function') {
                    chart.updateOptions(themeOptions);
                }
            });
            
            console.log(`Chart themes updated to ${isDark ? 'dark' : 'light'} mode`);
        },
        
        // Belirli bir grafiği güncelle
        updateChart: function(chartId, newData) {
            const chart = chartInstances[chartId];
            
            if (!chart) {
                console.warn(`Chart "${chartId}" not found. Cannot update.`);
                return false;
            }
            
            try {
                // Yeni seri verisi varsa güncelle
                if (newData.series) {
                    chart.updateSeries(newData.series);
                }
                
                // Yeni kategoriler varsa güncelle
                if (newData.categories) {
                    chart.updateOptions({
                        xaxis: {
                            categories: newData.categories
                        }
                    });
                }
                
                return true;
            } catch (error) {
                console.error(`Error updating chart "${chartId}":`, error);
                return false;
            }
        },
        
        // Belirli bir grafiği temizle
        destroyChart: function(chartId) {
            const chart = chartInstances[chartId];
            
            if (!chart) {
                return false;
            }
            
            try {
                chart.destroy();
                delete chartInstances[chartId];
                return true;
            } catch (error) {
                console.error(`Error destroying chart "${chartId}":`, error);
                return false;
            }
        }
    };
})();

/**
 * Yardımcı fonksiyonlar
 */

// Belirli bir fonksiyonu geciktiren debounce yardımcısı
function debounce(func, delay) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

// DOM hazırsa modülü başlat, değilse hazır olduğunda başlat
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // DOM hazır olduğunda grafik sistemini başlat
        window.VivaCRM = window.VivaCRM || {};
        window.VivaCRM.ChartSystem = ChartSystem;
        
        // Dashboard için hazırsa otomatik başlat
        if (document.querySelector('[data-chart-type]')) {
            ChartSystem.initialize().catch(console.error);
        }
    });
} else {
    // DOM zaten hazırsa hemen başlat
    window.VivaCRM = window.VivaCRM || {};
    window.VivaCRM.ChartSystem = ChartSystem;
    
    // Dashboard için hazırsa otomatik başlat
    if (document.querySelector('[data-chart-type]')) {
        ChartSystem.initialize().catch(console.error);
    }
}

// Modülü dışa aktar
export default ChartSystem;