// Alpine.js Components for VivaCRM

document.addEventListener('alpine:init', () => {
  // Notification Component
  Alpine.data('notification', () => ({
    notifications: [],
    visible: false,
    unreadCount: 0,

    init() {
      // Dummy data for demonstration
      this.notifications = [
        { id: 1, title: 'Yeni Sipariş', message: 'Yeni bir sipariş oluşturuldu', time: '5 dakika önce', read: false },
        { id: 2, title: 'Stok Uyarısı', message: 'Bazı ürünlerin stok miktarı azalıyor', time: '1 saat önce', read: false },
        { id: 3, title: 'Ödeme Bildirimi', message: 'Yeni bir ödeme alındı', time: '3 saat önce', read: true }
      ];
      this.updateUnreadCount();
    },

    toggle() {
      this.visible = !this.visible;
    },

    markAsRead(id) {
      const notification = this.notifications.find(n => n.id === id);
      if (notification) {
        notification.read = true;
        this.updateUnreadCount();
      }
    },

    markAllAsRead() {
      this.notifications.forEach(n => n.read = true);
      this.updateUnreadCount();
    },

    updateUnreadCount() {
      this.unreadCount = this.notifications.filter(n => !n.read).length;
    }
  }));

  // Search Component
  Alpine.data('search', () => ({
    query: '',
    showResults: false,
    results: [],
    isLoading: false,

    init() {
      this.$watch('query', value => {
        if (value.length >= 2) {
          this.search();
        } else {
          this.results = [];
          this.showResults = false;
        }
      });
    },

    search() {
      this.isLoading = true;
      this.showResults = true;
      
      // Simulate API call with setTimeout
      setTimeout(() => {
        // Sample results - in real app, this would come from an API
        if (this.query.length >= 2) {
          this.results = [
            { type: 'customer', id: 1, title: 'Ahmet Yılmaz', subtitle: 'Müşteri' },
            { type: 'product', id: 2, title: 'Akıllı Telefon X3', subtitle: 'Ürün' },
            { type: 'order', id: 3, title: 'Sipariş #10032', subtitle: 'Sipariş' }
          ];
        } else {
          this.results = [];
        }
        this.isLoading = false;
      }, 300);
    },

    reset() {
      this.query = '';
      this.results = [];
      this.showResults = false;
    }
  }));

  // Cart Component (for product selection in orders)
  Alpine.data('cart', () => ({
    items: [],
    total: 0,

    init() {
      // Load cart items from localStorage if available
      const savedCart = localStorage.getItem('vivacrm-cart');
      if (savedCart) {
        try {
          this.items = JSON.parse(savedCart);
          this.calculateTotal();
        } catch (e) {
          console.error('Error loading cart from localStorage', e);
          this.items = [];
          this.total = 0;
        }
      }
    },

    addItem(product, quantity = 1) {
      // Check if product already exists in cart
      const existingItem = this.items.find(item => item.id === product.id);
      if (existingItem) {
        existingItem.quantity += quantity;
      } else {
        this.items.push({
          id: product.id,
          name: product.name,
          price: product.price,
          quantity: quantity,
          subtotal: product.price * quantity
        });
      }
      this.saveCart();
      this.calculateTotal();
    },

    removeItem(id) {
      this.items = this.items.filter(item => item.id !== id);
      this.saveCart();
      this.calculateTotal();
    },

    updateQuantity(id, quantity) {
      const item = this.items.find(item => item.id === id);
      if (item) {
        item.quantity = quantity;
        item.subtotal = item.price * quantity;
        this.saveCart();
        this.calculateTotal();
      }
    },

    clearCart() {
      this.items = [];
      localStorage.removeItem('vivacrm-cart');
      this.total = 0;
    },

    calculateTotal() {
      this.total = this.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    },

    saveCart() {
      localStorage.setItem('vivacrm-cart', JSON.stringify(this.items));
    }
  }));

  // Dashboard Chart Component
  Alpine.data('dashboardChart', () => ({
    chart: null,

    init() {
      this.$nextTick(() => {
        this.initChart();
      });
    },

    initChart() {
      const chartElement = this.$el.querySelector('canvas');
      if (!chartElement) return;

      // Sample data - in a real app, this would come from the backend
      const labels = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran'];
      const data = {
        labels: labels,
        datasets: [
          {
            label: 'Satışlar',
            data: [12, 19, 3, 5, 2, 3],
            backgroundColor: 'rgba(49, 128, 255, 0.2)',
            borderColor: 'rgba(49, 128, 255, 1)',
            borderWidth: 1
          },
          {
            label: 'Giderler',
            data: [5, 10, 2, 3, 1, 2],
            backgroundColor: 'rgba(255, 165, 13, 0.2)',
            borderColor: 'rgba(255, 165, 13, 1)',
            borderWidth: 1
          }
        ]
      };

      // Check if Chart.js is available
      if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
      }

      // Initialize chart
      this.chart = new Chart(chartElement, {
        type: 'bar',
        data: data,
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'top',
            },
            title: {
              display: true,
              text: 'Satış ve Gider Grafiği'
            }
          }
        }
      });
    },

    updateChart(newData) {
      if (this.chart) {
        this.chart.data = newData;
        this.chart.update();
      }
    }
  }));

  // Filter Component
  Alpine.data('filter', () => ({
    filters: {},
    isOpen: false,

    init() {
      // Initialize filters from URL parameters if available
      const urlParams = new URLSearchParams(window.location.search);
      for (const [key, value] of urlParams.entries()) {
        this.filters[key] = value;
      }
    },

    toggle() {
      this.isOpen = !this.isOpen;
    },

    applyFilters() {
      // Build query string from filters
      const queryParams = new URLSearchParams();
      for (const [key, value] of Object.entries(this.filters)) {
        if (value) {
          queryParams.set(key, value);
        }
      }
      
      // Redirect to current URL with query parameters
      const newUrl = `${window.location.pathname}?${queryParams.toString()}`;
      window.location.href = newUrl;
    },

    resetFilters() {
      this.filters = {};
      // Redirect to current URL without query parameters
      window.location.href = window.location.pathname;
    }
  }));
});