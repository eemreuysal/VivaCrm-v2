/**
 * VivaCRM Dashboard Charts Fix
 * 
 * Bu dosya, dashboard grafiklerinin oluşturulması için doğrudan bir yaklaşım sağlar.
 * HTMX ile içerik yenilendikten sonra çalışır ve grafik elementlerini doğrudan kontrol eder.
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log('📊 Chart-Fix: Dashboard grafik düzeltici başlatılıyor...');
  
  // HTMX olaylarını dinle
  setupHtmxListeners();
  
  // Sayfa ilk yüklendiğinde grafikleri oluştur - DOM'un tamamen hazır olması için biraz bekleyelim
  setTimeout(function() {
    // Doğrudan grafikleri oluşturmaya çalış
    createCharts();
    
    // Ek güvenlik olarak, sayfa tamamen yüklendikten sonra (görüntüler vs dahil) bir kez daha deneyelim
    window.addEventListener('load', function() {
      console.log('📊 Chart-Fix: Sayfa tam yüklendi, grafikleri yeniden oluşturuluyor...');
      setTimeout(createCharts, 300);
    });
  }, 500);
});

/**
 * HTMX olay dinleyicilerini ekler
 */
function setupHtmxListeners() {
  // HTMX içerik yükleme işlemi tamamlandığında
  document.body.addEventListener('htmx:afterSwap', function(event) {
    console.log('📊 Chart-Fix: HTMX içerik yüklemesi algılandı, grafikler yenileniyor...');
    setTimeout(createCharts, 300);
  });
  
  // HTMX AJAX tamamlandığında (Bir element yenilendiğinde)
  document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.elt && event.detail.elt.closest('[data-chart-container]')) {
      console.log('📊 Chart-Fix: Grafik içeren element yenilendi, grafikler tekrar oluşturuluyor...');
      setTimeout(createCharts, 300);
    }
  });
  
  // Tema değişikliği dinleme
  document.addEventListener('vivacrm:theme-changed', function() {
    console.log('📊 Chart-Fix: Tema değişikliği tespit edildi');
    setTimeout(createCharts, 300);
  });
  
  // Eski tema değişikliği olayını da dinle
  document.addEventListener('theme-changed', function() {
    console.log('📊 Chart-Fix: Tema değişikliği tespit edildi (eski event)');
    setTimeout(createCharts, 300);
  });
  
  // Tab değişikliğini dinle (ayrı tab'larda grafikler var olabilir)
  document.addEventListener('click', function(e) {
    const clickedEl = e.target.closest('[role="tab"]');
    if (clickedEl) {
      console.log('📊 Chart-Fix: Tab değişikliği tespit edildi, 500ms sonra grafikler yenileniyor...');
      setTimeout(createCharts, 500);
    }
  });
  
  // Alpine.js x-show değişimlerini gözlemlemek için MutationObserver kullan
  // Bu HTMX olmadan yapılan DOM değişikliklerini de yakalar
  const observer = new MutationObserver(function(mutations) {
    let needsRefresh = false;
    
    mutations.forEach(function(mutation) {
      if (mutation.type === 'attributes' && 
          (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
        const target = mutation.target;
        // Eğer bu bir grafik konteyneri veya içeren bir element ise
        if (target.classList.contains('chart-container') || 
            target.querySelector('.chart-container') ||
            target.hasAttribute('data-chart-type') ||
            target.querySelector('[data-chart-type]')) {
          needsRefresh = true;
        }
      }
    });
    
    if (needsRefresh) {
      console.log('📊 Chart-Fix: DOM değişikliği tespit edildi (muhtemelen x-show), grafikler yenileniyor...');
      setTimeout(createCharts, 300);
    }
  });
  
  // DOM değişikliklerini gözlemle
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['style', 'class'],
    subtree: true,
    childList: true
  });
}

/**
 * Dashboard grafiklerini oluşturur
 * DOM elementlerini doğrudan kontrol eder ve görünür olduklarından emin olur
 */
function createCharts() {
  // Temiz log başlangıcı
  console.log('📊 Chart-Fix: Grafikler oluşturuluyor...');
  
  try {
    // ApexCharts kontrolü
    if (typeof ApexCharts === 'undefined') {
      console.error('📊 Chart-Fix: ApexCharts yüklü değil! Yüklemeye çalışılıyor...');
      // ApexCharts'ı dinamik olarak yüklemeye çalış
      loadApexCharts(function() {
        // Yükleme başarılı olduktan sonra grafikleri tekrar oluştur
        setTimeout(createCharts, 300);
      });
      return;
    }
    
    // Chart elementlerini bul
    const chartElements = document.querySelectorAll('[data-chart-type]');
    if (chartElements.length === 0) {
      console.log('📊 Chart-Fix: Hiçbir grafik elementi bulunamadı.');
      return;
    }
    
    console.log(`📊 Chart-Fix: ${chartElements.length} grafik elementi bulundu.`);
    
    // Sayfa boyutlara sahip mi kontrol et
    if (document.body.clientWidth === 0) {
      console.warn('📊 Chart-Fix: Sayfa boyutu henüz hesaplanmamış, grafikleri oluşturmak için bekletiliyor...');
      setTimeout(createCharts, 500);
      return;
    }
    
    // Her chart elementi için kontrol et ve oluştur
    let successCount = 0;
    chartElements.forEach((element, index) => {
      if (createSingleChart(element, index)) {
        successCount++;
      }
    });
    
    console.log(`📊 Chart-Fix: Toplam ${successCount}/${chartElements.length} grafik başarıyla oluşturuldu.`);
    
  } catch (error) {
    console.error('📊 Chart-Fix: Grafik oluşturma hatası:', error);
  }
}

/**
 * ApexCharts'ı dinamik olarak yükler
 */
function loadApexCharts(callback) {
  if (typeof ApexCharts !== 'undefined') {
    callback();
    return;
  }
  
  const script = document.createElement('script');
  script.src = '/static/js/vendor/apexcharts.min.js';
  script.async = true;
  script.onload = callback;
  script.onerror = function() {
    console.error('📊 Chart-Fix: ApexCharts yüklenemedi');
  };
  document.head.appendChild(script);
}

/**
 * Tek bir grafik elementini kontrol eder ve uygunsa grafiği oluşturur
 * @returns {boolean} Grafiğin başarıyla oluşturulup oluşturulmadığı
 */
function createSingleChart(element, index) {
  try {
    // Chart ID'sini al veya oluştur
    const chartId = element.id || `chart-${index}`;
    
    // Element görünür ve boyutları hesaplanabilir mi kontrol et
    if (!isElementReady(element)) {
      console.log(`📊 Chart-Fix: ${chartId} elementi hazır değil veya görünür değil. Atlıyor.`);
      return false;
    }
    
    // Data özelliklerini al
    const chartType = element.getAttribute('data-chart-type');
    let categories = [];
    let series = [];
    
    try {
      // JSON data özelliklerini parse et
      if (element.hasAttribute('data-categories')) {
        categories = JSON.parse(element.getAttribute('data-categories'));
      }
      
      if (element.hasAttribute('data-series')) {
        series = JSON.parse(element.getAttribute('data-series'));
      }
    } catch (parseError) {
      console.error(`📊 Chart-Fix: ${chartId} için veri parse hatası:`, parseError);
      return false;
    }
    
    // Veri doğrulama
    if (!series || (Array.isArray(series) && series.length === 0)) {
      console.warn(`📊 Chart-Fix: ${chartId} için veri yok veya boş. Atlıyor.`);
      return false;
    }
    
    // Grafik zaten varsa kaldır
    if (element._chart) {
      console.log(`📊 Chart-Fix: ${chartId} için var olan grafik kaldırılıyor...`);
      element._chart.destroy();
      element._chart = null;
    }
    
    // Tema ayarlarını al
    const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark' || 
                     document.documentElement.classList.contains('dark');
    
    // Grafik türüne göre seçenekler oluştur
    const options = createChartOptions(chartType, categories, series, isDarkMode);
    
    // Grafiği oluştur
    console.log(`📊 Chart-Fix: ${chartId} grafiği oluşturuluyor (${chartType})...`);
    
    // Width/height değerlerini options içinde de açıkça belirtelim
    options.chart.width = element._chartWidth || 300;
    options.chart.height = element._chartHeight || 300;
    
    try {
      const chart = new ApexCharts(element, options);
      
      // Grafiği renderla
      chart.render().then(() => {
        console.log(`📊 Chart-Fix: ${chartId} grafiği başarıyla oluşturuldu.`);
        // Referansı sakla (daha sonra güncellemek veya temizlemek için)
        element._chart = chart;
        return true;
      }).catch(error => {
        console.error(`📊 Chart-Fix: ${chartId} grafiği renderlanırken hata:`, error);
        return false;
      });
    } catch (renderError) {
      console.error(`📊 Chart-Fix: ${chartId} grafiği oluşturulurken hata:`, renderError);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error(`📊 Chart-Fix: Grafik #${index} oluşturma hatası:`, error);
    return false;
  }
}

/**
 * Element görünür ve doğru boyutta mu kontrol eder ve boyutlarını düzeltir
 */
function isElementReady(element) {
  if (!element) return false;
  
  // Element DOM'da var mı kontrol et
  if (!document.body.contains(element)) {
    console.warn(`📊 Chart-Fix: Element DOM'da bulunamadı`);
    return false;
  }
  
  // Element görünür mü kontrol et (display:none değil ve görünür alan içinde)
  const style = window.getComputedStyle(element);
  if (style.display === 'none' || style.visibility === 'hidden') {
    console.warn(`📊 Chart-Fix: Element görünür değil (display:${style.display}, visibility:${style.visibility})`);
    return false;
  }
  
  // Her zaman doğrudan boyut ekleyelim, ApexCharts NaN hatalarını önlemek için
  element.style.width = '100%';
  element.style.height = '300px';
  element.style.minWidth = '300px';
  element.style.minHeight = '300px';
  
  // Boyutları zorla - NaN hatalarını önlemek için
  element.setAttribute('data-width', '100%');
  element.setAttribute('data-height', '300');

  // Boyutları kontrol edelim
  const rect = element.getBoundingClientRect();
  const width = rect.width || element.offsetWidth || 300;
  const height = rect.height || element.offsetHeight || 300;
  
  // Loglama için
  console.log(`📊 Chart-Fix: Element boyutları - width:${width}, height:${height}`);
  
  // Boyutlar hesaplanamadıysa bile görünür ve DOM'da varsa, hardcoded değerler kullanırız
  if (width <= 10 || height <= 10) {
    console.warn(`📊 Chart-Fix: Element boyutları çok küçük, sabit değerler kullanılacak`);
    element._chartWidth = 300;
    element._chartHeight = 300;
    return true; // Her durumda devam ediyoruz, sabit değerler kullanacağız
  }
  
  // Doğru boyutları kaydedelim
  element._chartWidth = width;
  element._chartHeight = height;
  return true;
}

/**
 * Grafik türüne göre ApexCharts seçenekleri oluşturur
 */
function createChartOptions(chartType, categories, series, isDarkMode) {
  // Tema renklerini belirle
  const colors = isDarkMode
    ? ['#4ade80', '#38bdf8', '#fbbf24', '#c084fc']  // Koyu tema renkleri
    : ['#22c55e', '#0ea5e9', '#f59e0b', '#a855f7']; // Açık tema renkleri
  
  // Ortak ayarlar
  const baseOptions = {
    colors: colors,
    chart: {
      height: 300, // Varsayılan sabit değer - daha sonra element._chartHeight ile değiştirilecek
      width: 300, // Varsayılan sabit değer - daha sonra element._chartWidth ile değiştirilecek
      type: 'line', // Varsayılan tip
      background: 'transparent',
      toolbar: {
        show: false,
      },
      animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 350
      },
      fontFamily: 'Inter, sans-serif',
      redrawOnWindowResize: true,
      redrawOnParentResize: true,
    },
    stroke: {
      curve: 'smooth',
      width: 3,
    },
    xaxis: {
      categories: categories,
      labels: {
        style: {
          colors: isDarkMode ? '#d1d5db' : '#374151',
          fontFamily: 'Inter, sans-serif',
        },
      },
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false, 
      },
    },
    yaxis: {
      labels: {
        style: {
          colors: isDarkMode ? '#d1d5db' : '#374151',
          fontFamily: 'Inter, sans-serif',
        },
        formatter: function(value) {
          return value.toLocaleString('tr-TR');
        }
      }
    },
    grid: {
      show: true,
      borderColor: isDarkMode ? '#334155' : '#e5e7eb',
      strokeDashArray: 4,
      position: 'back',
    },
    tooltip: {
      enabled: true,
      theme: isDarkMode ? 'dark' : 'light',
      style: {
        fontFamily: 'Inter, sans-serif',
      },
      y: {
        formatter: function(value) {
          return value.toLocaleString('tr-TR');
        }
      }
    },
    legend: {
      position: 'top',
      horizontalAlign: 'right',
      labels: {
        colors: isDarkMode ? '#d1d5db' : '#374151',
      }
    },
    markers: {
      size: 5,
      strokeWidth: 0,
      hover: {
        size: 7,
      }
    },
    responsive: [
      {
        breakpoint: 640,
        options: {
          chart: {
            height: 240,
          },
          legend: {
            position: 'bottom',
            horizontalAlign: 'center',
          }
        }
      }
    ]
  };
  
  // Grafik türüne özel ayarlar
  switch (chartType) {
    case 'sales':
      return {
        ...baseOptions,
        chart: {
          ...baseOptions.chart,
          type: 'area',
        },
        dataLabels: {
          enabled: false
        },
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.7,
            opacityTo: 0.2,
            stops: [0, 90, 100]
          }
        },
        series: Array.isArray(series) && !Array.isArray(series[0]) ? 
          [{ name: 'Satışlar', data: series }] : 
          series,
      };
      
    case 'orders':
      return {
        ...baseOptions,
        chart: {
          ...baseOptions.chart,
          type: 'bar',
        },
        plotOptions: {
          bar: {
            borderRadius: 4,
            horizontal: false,
            columnWidth: '60%',
          }
        },
        dataLabels: {
          enabled: false
        },
        series: Array.isArray(series) && !Array.isArray(series[0]) ? 
          [{ name: 'Siparişler', data: series }] : 
          series,
      };
      
    case 'customers':
      return {
        ...baseOptions,
        chart: {
          ...baseOptions.chart,
          type: 'line'
        },
        stroke: {
          curve: 'straight'
        },
        series: Array.isArray(series) && !Array.isArray(series[0]) ? 
          [{ name: 'Müşteriler', data: series }] : 
          series,
      };
      
    case 'revenue_comparison':
      return {
        ...baseOptions,
        chart: {
          ...baseOptions.chart,
          type: 'line',
        },
        dataLabels: {
          enabled: false
        },
        series: Array.isArray(series) && Array.isArray(series[0]) ? 
          [
            { name: 'Bu Ay', data: series[0] || [] },
            { name: 'Geçen Ay', data: series[1] || [] }
          ] : 
          (Array.isArray(series) && !Array.isArray(series[0]) ? 
            [{ name: 'Gelir', data: series }] : 
            series),
      };
      
    case 'category':
    case 'product_distribution':
      return {
        ...baseOptions,
        chart: {
          ...baseOptions.chart,
          type: 'pie',
        },
        labels: categories,
        legend: {
          position: 'bottom',
        },
        series: series,
        responsive: [
          {
            breakpoint: 640,
            options: {
              chart: {
                height: 300,
              },
              legend: {
                position: 'bottom',
                horizontalAlign: 'center',
              }
            }
          }
        ]
      };
      
    default:
      // Varsayılan line chart
      return {
        ...baseOptions,
        series: Array.isArray(series) && !Array.isArray(series[0]) ? 
          [{ name: 'Veri', data: series }] : 
          series,
      };
  }
}

/**
 * Global API - Harici koddan çağrılabilir
 */
window.vivaChartFix = {
  // Tüm grafikleri yeniden oluştur
  refreshCharts: function() {
    console.log('📊 Chart-Fix API: refreshCharts çağrıldı');
    createCharts();
  },
  
  // Belirli bir grafik ID'sini yeniden oluştur
  refreshChart: function(chartId) {
    const element = document.getElementById(chartId);
    if (element) {
      console.log(`📊 Chart-Fix API: ${chartId} grafiği yenileniyor`);
      createSingleChart(element, 0);
    } else {
      console.error(`📊 Chart-Fix API: ${chartId} ID'li element bulunamadı`);
    }
  },
  
  // Tüm grafikleri belirli bir tema ile yeniden oluştur
  updateTheme: function(isDarkMode) {
    console.log(`📊 Chart-Fix API: Tüm grafikler ${isDarkMode ? 'koyu' : 'açık'} tema için güncelleniyor`);
    createCharts();
  }
};