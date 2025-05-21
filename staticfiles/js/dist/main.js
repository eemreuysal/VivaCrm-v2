// VivaCRM main.js - Dashboard scripts integration
// Global olarak Alpine ve HTMX'i tanımla
window.Alpine = window.Alpine || {};
window.htmx = window.htmx || { 
    on: function() {}, 
    off: function() {},
    trigger: function() {},
    ajax: function() {}
};

// Helper fonksiyon - DOM yüklendikten sonra çalıştır
function onDOMReady(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

// VivaCRM store ve utilities
window.vivaCRM = window.vivaCRM || {
    store: {
        get: function(key) { return localStorage.getItem('vivacrm-' + key); },
        set: function(key, value) { localStorage.setItem('vivacrm-' + key, value); },
        cache: function(key, value, ttl) { 
            localStorage.setItem('vivacrm-cache-' + key, JSON.stringify({
                value: value,
                expires: Date.now() + (ttl || 60000)
            }));
        },
        addNotification: function(notification) {
            console.log('Notification:', notification);
        }
    },
    utils: {
        formatDate: function(date) {
            return new Date(date).toLocaleDateString('tr-TR');
        },
        formatCurrency: function(value) {
            return new Intl.NumberFormat('tr-TR', {
                style: 'currency',
                currency: 'TRY'
            }).format(value);
        }
    },
    createAlpineComponent: function(definition) {
        return function() {
            return {
                init: function() { 
                    if (definition.init) {
                        definition.init.call(this);
                    }
                },
                destroy: function() {
                    if (definition.destroy) {
                        definition.destroy.call(this);
                    }
                },
                ...definition
            };
        };
    }
};

// Dashboard sayfasını initialize et
onDOMReady(function() {
    if (document.getElementById('dashboard-content')) {
        console.log('Dashboard sayfası yükleniyor...');

        // Burada dashboard sayfası için özel kodlar çalışabilir
        if (window.Alpine) {
            // Bileşenleri tanımla
            window.ordersTableApp = function() {
                return {
                    filterStatus: '',
                    sortColumn: 'id',
                    sortDirection: 'asc',
                    
                    init() {
                        console.log('Orders table component initialized');
                    },
                    
                    sortBy(column) {
                        if (this.sortColumn === column) {
                            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
                        } else {
                            this.sortColumn = column;
                            this.sortDirection = 'asc';
                        }
                    }
                };
            };

            window.lowStockApp = function() {
                return {
                    showAll: false,
                    
                    init() {
                        console.log('Low stock component initialized');
                    }
                };
            };

            window.dateFilterComponent = function() {
                return {
                    showDatePicker: false,
                    customStartDate: null,
                    customEndDate: null,
                    
                    init() {
                        console.log('Date filter component initialized');
                        
                        if (window.dashboardInitData) {
                            this.customStartDate = window.dashboardInitData.customStartDate || null;
                            this.customEndDate = window.dashboardInitData.customEndDate || null;
                        }
                    },
                    
                    applyCustomDateRange() {
                        if (!this.customStartDate || !this.customEndDate) {
                            alert('Lütfen başlangıç ve bitiş tarihlerini seçin');
                            return;
                        }
                        
                        this.showDatePicker = false;
                        
                        if (window.location.href.includes('dashboard')) {
                            window.location.href = `/dashboard/?period=custom&start_date=${this.customStartDate}&end_date=${this.customEndDate}`;
                        }
                    },
                    
                    formatDate(dateString) {
                        if (!dateString) return '';
                        return new Intl.DateTimeFormat('tr-TR').format(new Date(dateString));
                    }
                };
            };

            window.dashboardComponent = function() {
                return {
                    currentPeriod: 'month',
                    loading: false,
                    showDatePicker: false,
                    customStartDate: null,
                    customEndDate: null,
                    charts: new Map(),
                    notificationOpen: false,
                    darkMode: localStorage.getItem('theme') === 'dark',

                    init() {
                        if (window.dashboardInitData) {
                            this.currentPeriod = window.dashboardInitData.currentPeriod || 'month';
                            this.customStartDate = window.dashboardInitData.customStartDate || null;
                            this.customEndDate = window.dashboardInitData.customEndDate || null;
                        }
                        
                        this.setupEventListeners();
                    },

                    toggleTheme() {
                        if (window.Alpine && window.Alpine.store('theme')) {
                            window.Alpine.store('theme').toggle();
                            this.darkMode = window.Alpine.store('theme').darkMode;
                        } else {
                            this.darkMode = !this.darkMode;
                            localStorage.setItem('vivacrm-theme', this.darkMode ? 'dark' : 'light');
                            document.documentElement.setAttribute('data-theme', this.darkMode ? 'vivacrmDark' : 'vivacrm');
                            document.documentElement.classList.toggle('dark', this.darkMode);
                        }
                    },

                    setPeriod(period) {
                        this.currentPeriod = period;
                        this.showDatePicker = false;
                        this.refreshData();
                    },
                    
                    applyCustomDate(startDate, endDate) {
                        this.customStartDate = startDate;
                        this.customEndDate = endDate;
                        this.refreshData();
                    },

                    async refreshData() {
                        this.loading = true;

                        try {
                            let url = `/dashboard/?period=${this.currentPeriod}`;
                            
                            if (this.currentPeriod === 'custom' && this.customStartDate && this.customEndDate) {
                                url += `&start_date=${this.customStartDate}&end_date=${this.customEndDate}`;
                            }
                            
                            window.location.href = url;
                        } catch (error) {
                            console.error('Failed to refresh dashboard data:', error);
                        }
                    },

                    setupEventListeners() {
                        document.addEventListener('htmx:afterSettle', (event) => {
                            if (event.detail.target.id === 'dashboard-content') {
                                this.loading = false;
                            }
                        });
                    },

                    formatDate(date) {
                        return new Intl.DateTimeFormat('tr-TR').format(new Date(date));
                    },

                    formatCurrency(value) {
                        return new Intl.NumberFormat('tr-TR', {
                            style: 'currency',
                            currency: 'TRY'
                        }).format(value);
                    }
                };
            };

            // Alpine'ı başlat
            if (!window.Alpine.initialized) {
                if (typeof Alpine.data === 'function') {
                    Alpine.data('dashboardComponent', window.dashboardComponent);
                    Alpine.data('ordersTableApp', window.ordersTableApp);
                    Alpine.data('lowStockApp', window.lowStockApp);
                    Alpine.data('dateFilterComponent', window.dateFilterComponent);
                }
                
                if (typeof Alpine.start === 'function' && !window._alpine_initialized) {
                    Alpine.start();
                    window._alpine_initialized = true;
                }
            }
        }
    }
});