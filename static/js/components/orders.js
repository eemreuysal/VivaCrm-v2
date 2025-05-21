// VivaCRM - Orders Component
import { store } from '../store/index.js';
import { createAlpineComponent } from '../core/base-component.js';
import { utils } from '../core/utils.js';

export const ordersComponent = () => createAlpineComponent({
    // State
    sortField: 'order_date',
    sortDirection: 'desc',
    filterStatus: 'all',
    searchQuery: '',
    selectedOrders: new Set(),
    loading: false,

    init() {
        this.setupSearch();
        this.loadSavedState();

        // Subscribe to notifications - otomatik temizlenecek
        this.subscribe('notifications', (notifications) => {
            // Handle order-specific notifications
            const orderNotification = notifications.find((n) => n.type === 'order-update');
            if (orderNotification) {
                this.refreshTable();
            }
        });
    },

    destroy() {
        this.saveState();
        // Base component cleanup otomatik yapılacak
    },

    setupSearch() {
        this.$watch('searchQuery', utils.debounce((value) => {
            this.search(value);
        }, 300));
    },

    loadSavedState() {
        const savedState = store.getCache('orders-table-state');
        if (savedState) {
            this.sortField = savedState.sortField || this.sortField;
            this.sortDirection = savedState.sortDirection || this.sortDirection;
            this.filterStatus = savedState.filterStatus || this.filterStatus;
        }
    },

    saveState() {
        store.cache(
            'orders-table-state',
            {
                sortField: this.sortField,
                sortDirection: this.sortDirection,
                filterStatus: this.filterStatus
            },
            1000 * 60 * 30
        ); // 30 minutes
    },

    sort(field) {
        if (this.sortField === field) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortField = field;
            this.sortDirection = 'asc';
        }
        this.refreshTable();
    },

    filter(status) {
        this.filterStatus = status;
        this.refreshTable();
    },

    async search(query) {
        this.loading = true;
        try {
            await htmx.ajax('GET', `/orders/search/?q=${encodeURIComponent(query)}`, {
                target: '#orders-table',
                swap: 'innerHTML'
            });
        } catch (error) {
            console.error('Search error:', error);
            store.addNotification({
                type: 'error',
                message: 'Arama başarısız oldu',
                timeout: 5000
            });
        } finally {
            this.loading = false;
        }
    },

    async refreshTable() {
        this.loading = true;
        const params = new URLSearchParams({
            sort: this.sortField,
            direction: this.sortDirection,
            status: this.filterStatus,
            q: this.searchQuery
        });

        try {
            await htmx.ajax('GET', `/orders/table/?${params}`, {
                target: '#orders-table',
                swap: 'innerHTML'
            });
            this.saveState();
        } catch (error) {
            console.error('Refresh error:', error);
            store.addNotification({
                type: 'error',
                message: 'Tablo yenilenirken hata oluştu',
                timeout: 5000
            });
        } finally {
            this.loading = false;
        }
    },

    selectOrder(orderId) {
        if (this.selectedOrders.has(orderId)) {
            this.selectedOrders.delete(orderId);
        } else {
            this.selectedOrders.add(orderId);
        }
    },

    selectAll(checked) {
        const orderElements = document.querySelectorAll('[data-order-id]');
        if (checked) {
            orderElements.forEach((el) => {
                const orderId = el.dataset.orderId;
                this.selectedOrders.add(orderId);
            });
        } else {
            this.selectedOrders.clear();
        }
    },

    async bulkAction(action) {
        if (this.selectedOrders.size === 0) {
            store.addNotification({
                type: 'warning',
                message: 'Lütfen en az bir sipariş seçin',
                timeout: 3000
            });
            return;
        }

        const orderIds = Array.from(this.selectedOrders);

        try {
            const response = await fetch('/orders/bulk-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.VivaCRM?.csrfToken || ''
                },
                body: JSON.stringify({
                    action: action,
                    order_ids: orderIds
                })
            });

            if (response.ok) {
                const result = await response.json();
                store.addNotification({
                    type: 'success',
                    message: result.message || 'İşlem başarılı',
                    timeout: 5000
                });
                this.selectedOrders.clear();
                this.refreshTable();
            } else {
                throw new Error('Bulk action failed');
            }
        } catch (error) {
            console.error('Bulk action error:', error);
            store.addNotification({
                type: 'error',
                message: 'Toplu işlem başarısız oldu',
                timeout: 5000
            });
        }
    }
});

// Register with Alpine
if (window.Alpine) {
    Alpine.data('ordersComponent', ordersComponent);
}

// Export for module usage
export default {
    init: () => {
        // Orders component loaded successfully
    }
};
