// VivaCRM - Chart Manager Module
// Store bağımlılığını kaldırdık, event-based yaklaşım kullanacağız

export class ChartManager {
    constructor() {
        this.charts = new Map();
        this.chartLibrary = null;
        this.defaultOptions = this.getDefaultOptions();
    }

    /**
     * Initialize chart library
     */
    async initializeLibrary() {
        if (this.chartLibrary) return this.chartLibrary;

        try {
            // Dynamically import ApexCharts
            await import('https://cdn.jsdelivr.net/npm/apexcharts@latest/dist/apexcharts.min.js');
            this.chartLibrary = window.ApexCharts;
            return this.chartLibrary;
        } catch (error) {
            console.error('Failed to load chart library:', error);
            throw error;
        }
    }

    /**
     * Create a new chart
     * @param {HTMLElement} element - DOM element
     * @param {Object} config - Chart configuration
     * @returns {Promise<Object>} Chart instance
     */
    async createChart(element, config) {
        await this.initializeLibrary();

        const chartOptions = {
            ...this.defaultOptions,
            ...config.options,
            chart: {
                ...this.defaultOptions.chart,
                ...config.options?.chart,
                type: config.type,
                height: config.height || 350
            }
        };

        // Apply theme
        this.applyTheme(chartOptions);

        const chart = new this.chartLibrary(element, chartOptions);
        await chart.render();

        this.charts.set(config.id, chart);
        return chart;
    }

    /**
     * Update chart data
     * @param {string} chartId - Chart ID
     * @param {Object} data - New data
     */
    async updateChart(chartId, data) {
        const chart = this.charts.get(chartId);
        if (!chart) {
            console.error(`Chart not found: ${chartId}`);
            return;
        }

        await chart.updateOptions({
            series: data.series,
            labels: data.labels
        });
    }

    /**
     * Destroy a chart
     * @param {string} chartId - Chart ID
     */
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartId);
        }
    }

    /**
     * Destroy all charts
     */
    destroyAll() {
        this.charts.forEach((chart) => chart.destroy());
        this.charts.clear();
    }

    /**
     * Get default chart options
     */
    getDefaultOptions() {
        return {
            chart: {
                fontFamily: 'Inter, system-ui, sans-serif',
                toolbar: {
                    show: false
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800
                }
            },
            colors: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'],
            dataLabels: {
                enabled: false
            },
            stroke: {
                curve: 'smooth',
                width: 3
            },
            grid: {
                borderColor: '#e5e7eb',
                strokeDashArray: 0
            },
            tooltip: {
                theme: 'light',
                style: {
                    fontSize: '12px'
                }
            },
            responsive: [
                {
                    breakpoint: 768,
                    options: {
                        chart: {
                            height: 300
                        }
                    }
                }
            ]
        };
    }

    /**
     * Apply theme to chart options
     * @param {Object} options - Chart options
     */
    applyTheme(options) {
        // Theme'i HTML data attribute'dan oku
        const theme = document.documentElement.getAttribute('data-theme') || 'light';
        const isDark = theme === 'vivacrmDark' || theme === 'dark';

        if (isDark) {
            options.theme = {
                mode: 'dark'
            };
            options.grid.borderColor = '#374151';
            options.tooltip.theme = 'dark';
        }
    }

    /**
     * Export chart as image
     * @param {string} chartId - Chart ID
     * @param {string} format - Export format (png, svg)
     */
    async exportChart(chartId, format = 'png') {
        const chart = this.charts.get(chartId);
        if (!chart) {
            console.error(`Chart not found: ${chartId}`);
            return;
        }

        if (format === 'png') {
            await chart.dataURI().then(({ imgURI }) => {
                const link = document.createElement('a');
                link.href = imgURI;
                link.download = `chart-${chartId}-${Date.now()}.png`;
                link.click();
            });
        } else if (format === 'svg') {
            await chart.saveSvg().then((svgString) => {
                const blob = new Blob([svgString], { type: 'image/svg+xml' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `chart-${chartId}-${Date.now()}.svg`;
                link.click();
                URL.revokeObjectURL(url);
            });
        }
    }

    /**
     * Update all charts theme
     */
    updateAllChartsTheme() {
        this.charts.forEach((chart) => {
            const options = { ...this.defaultOptions };
            this.applyTheme(options);
            chart.updateOptions(options);
        });
    }
}

// Theme değişikliklerini dinlemek için event listener kullan
document.addEventListener('vivacrm:theme-changed', (_event) => {
    const chartManager = new ChartManager();
    chartManager.updateAllChartsTheme();
});

// Export for direct usage
export default ChartManager;
