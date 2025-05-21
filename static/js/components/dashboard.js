/**
 * VivaCRM Dashboard - Main JS
 *
 * Bu dosya dashboard bileşenlerinin Alpine.js ile kaydını yapar
 * ve HTMX entegrasyonunu yönetir.
 */

import { dashboardComponent, dateFilterComponent } from './dashboard-components.js';

// Main.js için export edilen bileşen
export { dashboardComponent };

// Alpine.js bileşenleri kaydet
document.addEventListener('DOMContentLoaded', () => {
    if (window.Alpine) {
    // Dashboard ana bileşenleri
        window.Alpine.data('dashboardComponent', dashboardComponent);
        window.Alpine.data('dateFilterComponent', dateFilterComponent);

        // HTMX entegrasyonu için olay işleyicileri
        setupHtmxEvents();
    }
});

/**
 * HTMX olay işleyicilerini ayarlar
 */
function setupHtmxEvents() {
    // HTMX ile çalışacak sonradan eklenen dinamik elementler için eventler dinle
    document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.detail.target.id === 'dashboard-content') {
            // İstatistik ve grafik elementleri sonradan yüklenmiş olabilir
            // Yeni eklenen elementlerde Alpine.js'i başlat
            if (window.Alpine && window.Alpine.initTree) {
                window.Alpine.initTree(event.detail.target);
            }
        }
    });

    // HTMX değerleri filtrelemek için olay ekle
    document.body.addEventListener('periodChanged', (_event) => {
    // Ana dashboard komponentinden değerleri al
        const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
        if (dashboardEl && dashboardEl.__x) {
            const component = dashboardEl.__x.$data;

            // Dashboard içeriğini bul
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

                // URL'i güncelle (pushState ile)
                const newUrl = new URL(window.location.href);
                newUrl.search = params.toString();
                window.history.pushState({}, '', newUrl.toString());

                // HTMX isteğini tetikle
                window.htmx.trigger(dashboardContent, 'htmx:load', {});
            }
        }
    });

    // Tema değişikliği olaylarını dinle ve grafiklere ilet
    window.addEventListener('theme-changed', () => {
        const event = new CustomEvent('updateChartsTheme');
        document.dispatchEvent(event);
    });
}

/**
 * Grafik verilerini yüklemek için yardımcı fonksiyon
 * Bu fonksiyon gerektiğinde chart_card bileşenlerinden çağrılabilir
 *
 * @param {string} chartId - Grafik elementi ID'si
 * @param {string} chartType - Grafik türü (sales, category, orders)
 */
export function loadDashboardChart(chartId, chartType) {
    const chartEl = document.getElementById(chartId);
    if (!chartEl) return;

    // Grafik bileşeninin verilerini kontrol et
    if (!chartEl.dataset.series || !chartEl.dataset.categories) {
    // Verileri API'dan al
        fetch(`/dashboard/api/chart/${chartType}/`)
            .then((response) => response.json())
            .then((data) => {
                // Dataset özelliklerini güncelle
                chartEl.dataset.series = JSON.stringify(data.series);
                chartEl.dataset.categories = JSON.stringify(data.categories);

                // Alpine.js bileşeninde grafik yenilemeyi tetikle
                const dashboardEl = document.querySelector('[x-data="dashboardComponent()"]');
                if (dashboardEl && dashboardEl.__x) {
                    dashboardEl.__x.$data.initializeCharts();
                }
            })
            .catch((error) => {
                console.error('Grafik verisi yükleme hatası:', error);
            });
    }
}
