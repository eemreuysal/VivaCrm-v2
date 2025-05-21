/**
 * VivaCRM - Alpine.js Sipariş Tablosu Bileşeni
 * 
 * Dashboard ve diğer sayfalarda sipariş tablosunu yönetmek için kullanılan bileşen.
 * Sipariş verilerini filtreler, sıralar ve görüntüler.
 */

import { createLogger } from '../../core/utils.js';

// Logger oluştur
const logger = createLogger('OrdersTable', {
  emoji: '📦'
});

/**
 * Sipariş tablosu bileşeni
 * Sipariş verilerini filtreler ve görüntüler
 * 
 * @returns {Object} Alpine.js bileşen nesnesi
 */
export function ordersTableComponent() {
  return {
    // Durum değişkenleri
    orders: [],
    filteredOrders: [],
    loading: false,
    searchTerm: '',
    sortField: 'order_date',
    sortDirection: 'desc',
    
    // Yaşam döngüsü metodu
    init() {
      // Tablo elemanından sipariş verilerini al
      const ordersTable = document.getElementById('ordersTable');
      if (ordersTable && ordersTable.dataset.orders) {
        try {
          this.orders = JSON.parse(ordersTable.dataset.orders);
          this.filteredOrders = [...this.orders];
          logger.debug(`Sipariş tablosu yüklendi, ${this.orders.length} sipariş bulundu`);
        } catch (e) {
          logger.error(`Sipariş verisi ayrıştırma hatası: ${e.message}`);
          this.orders = [];
          this.filteredOrders = [];
        }
      } else {
        logger.warn('Sipariş verisi bulunamadı, boş tablo gösteriliyor');
        this.orders = [];
        this.filteredOrders = [];
      }
    },
    
    // Siparişleri arama terimine göre filtrele
    filterOrders() {
      if (!this.searchTerm.trim()) {
        this.filteredOrders = [...this.orders];
        return;
      }
      
      const term = this.searchTerm.toLowerCase().trim();
      this.filteredOrders = this.orders.filter(order => {
        return (
          order.order_number?.toLowerCase().includes(term) ||
          order.customer_name?.toLowerCase().includes(term) ||
          order.status?.toLowerCase().includes(term)
        );
      });
      
      logger.debug(`Siparişler filtrelendi, aranan: "${term}", sonuç: ${this.filteredOrders.length} sipariş`);
    },
    
    // Siparişleri belirtilen alana göre sırala
    sortOrders(field) {
      if (this.sortField === field) {
        // Aynı alana tekrar tıklandıysa sıralama yönünü değiştir
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        // Farklı bir alana tıklandıysa sıralama alanını değiştir ve azalan sıralama yap
        this.sortField = field;
        this.sortDirection = 'desc';
      }
      
      // Siparişleri sırala
      this.filteredOrders.sort((a, b) => {
        let aValue = a[field];
        let bValue = b[field];
        
        // Tarih alanları için özel işlem
        if (field === 'order_date' || field === 'delivery_date') {
          aValue = new Date(aValue);
          bValue = new Date(bValue);
        }
        
        // Sayısal alanlar için özel işlem
        if (field === 'total_amount') {
          aValue = parseFloat(aValue);
          bValue = parseFloat(bValue);
        }
        
        // Sıralama yönüne göre karşılaştır
        if (this.sortDirection === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
      
      logger.debug(`Siparişler sıralandı, alan: ${field}, yön: ${this.sortDirection}`);
    },
    
    // Sipariş ayrıntılarını görüntüle
    viewOrderDetails(orderId) {
      logger.debug(`Sipariş ayrıntıları görüntüleniyor, ID: ${orderId}`);
      window.location.href = `/orders/${orderId}/`;
    },
    
    // Siparişi düzenleme sayfasına git
    editOrder(orderId) {
      logger.debug(`Sipariş düzenleniyor, ID: ${orderId}`);
      window.location.href = `/orders/${orderId}/edit/`;
    },
    
    // Sipariş durumunu güncelle
    updateOrderStatus(orderId, status) {
      logger.debug(`Sipariş durumu güncelleniyor, ID: ${orderId}, yeni durum: ${status}`);
      
      // HTMX isteği gönder (eğer varsa)
      const updateForm = document.getElementById('order-status-form');
      if (updateForm && window.htmx) {
        updateForm.querySelector('input[name="order_id"]').value = orderId;
        updateForm.querySelector('input[name="status"]').value = status;
        window.htmx.trigger(updateForm, 'submit');
      } else {
        // Fallback: Düzenleme sayfasına git
        window.location.href = `/orders/${orderId}/edit/?status=${status}`;
      }
    },
    
    // Sipariş durumuna göre rozet sınıfı döndür
    getStatusClass(status) {
      const statusMap = {
        'pending': 'badge-warning',
        'processing': 'badge-info',
        'shipped': 'badge-primary',
        'delivered': 'badge-success',
        'cancelled': 'badge-error'
      };
      
      return statusMap[status?.toLowerCase()] || 'badge-secondary';
    },
    
    // Para birimini formatla
    formatCurrency(amount) {
      if (amount === null || amount === undefined) return '';
      
      // Global formatCurrency fonksiyonunu kullan (eğer varsa)
      if (window.formatCurrency) {
        return window.formatCurrency(amount);
      }
      
      // Fallback: Yerel formatla
      return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    },
    
    // Tarihi formatla
    formatDate(dateStr) {
      if (!dateStr) return '';
      
      // Global formatDate fonksiyonunu kullan (eğer varsa)
      if (window.formatDate) {
        return window.formatDate(dateStr);
      }
      
      // Fallback: Yerel formatla
      try {
        return new Date(dateStr).toLocaleDateString('tr-TR', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      } catch (e) {
        logger.error(`Tarih formatı hatası: ${e.message}`);
        return dateStr;
      }
    }
  };
}

// ES modül olarak dışa aktar
export default ordersTableComponent;