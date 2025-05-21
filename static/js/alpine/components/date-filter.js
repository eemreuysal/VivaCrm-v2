/**
 * VivaCRM - Alpine.js Tarih Filtresi Bileşeni
 * 
 * Dashboard ve diğer sayfalarda tarih aralığı seçimi yapmak için kullanılan bileşen.
 * Özel tarih aralıkları ve hazır periyot seçimleri için kullanılır.
 */

import { createLogger } from '../../core/utils.js';

// Logger oluştur
const logger = createLogger('DateFilter', {
  emoji: '📅'
});

/**
 * Tarih filtresi bileşeni
 * Özel tarih aralıkları seçmeyi sağlar
 * 
 * @returns {Object} Alpine.js bileşen nesnesi
 */
export function dateFilterComponent() {
  return {
    // Durum değişkenleri
    showDatePicker: false,
    startDate: null,
    endDate: null,
    
    // Yaşam döngüsü metodu
    init() {
      // Üst dashboard bileşeninden tarih değerlerini al
      if (this.$root.customStartDate) {
        this.startDate = this.$root.customStartDate;
      }
      
      if (this.$root.customEndDate) {
        this.endDate = this.$root.customEndDate;
      }
      
      logger.debug('Tarih filtresi bileşeni başlatıldı');
    },
    
    // Tarih seçici görünürlüğünü değiştir
    toggleDatePicker() {
      this.showDatePicker = !this.showDatePicker;
    },
    
    // Özel tarih aralığını uygula
    applyCustomDateRange() {
      if (!this.startDate || !this.endDate) {
        alert('Lütfen başlangıç ve bitiş tarihlerini seçin');
        return;
      }
      
      // Tarihleri doğrula
      const startDate = new Date(this.startDate);
      const endDate = new Date(this.endDate);
      
      if (startDate > endDate) {
        alert('Başlangıç tarihi bitiş tarihinden sonra olamaz');
        return;
      }
      
      // Üst bileşene uygula
      this.$root.customStartDate = this.startDate;
      this.$root.customEndDate = this.endDate;
      this.$root.setPeriod('custom');
      
      // Tarih seçiciyi kapat
      this.showDatePicker = false;
      
      logger.debug(`Özel tarih aralığı uygulandı: ${this.startDate} - ${this.endDate}`);
    },
    
    // Son ay için hazır ayar
    setLastMonth() {
      const today = new Date();
      const lastMonth = new Date(today);
      lastMonth.setMonth(today.getMonth() - 1);
      
      this.startDate = this.formatDateForInput(lastMonth);
      this.endDate = this.formatDateForInput(today);
      
      this.applyCustomDateRange();
      
      logger.debug('Son ay filtresi uygulandı');
    },
    
    // Son çeyrek için hazır ayar
    setLastQuarter() {
      const today = new Date();
      const lastQuarter = new Date(today);
      lastQuarter.setMonth(today.getMonth() - 3);
      
      this.startDate = this.formatDateForInput(lastQuarter);
      this.endDate = this.formatDateForInput(today);
      
      this.applyCustomDateRange();
      
      logger.debug('Son çeyrek filtresi uygulandı');
    },
    
    // Son yıl için hazır ayar
    setLastYear() {
      const today = new Date();
      const lastYear = new Date(today);
      lastYear.setFullYear(today.getFullYear() - 1);
      
      this.startDate = this.formatDateForInput(lastYear);
      this.endDate = this.formatDateForInput(today);
      
      this.applyCustomDateRange();
      
      logger.debug('Son yıl filtresi uygulandı');
    },
    
    // Bu ay için hazır ayar
    setThisMonth() {
      const today = new Date();
      const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
      
      this.startDate = this.formatDateForInput(firstDay);
      this.endDate = this.formatDateForInput(today);
      
      this.applyCustomDateRange();
      
      logger.debug('Bu ay filtresi uygulandı');
    },
    
    // Bu hafta için hazır ayar
    setThisWeek() {
      const today = new Date();
      const firstDay = new Date(today);
      const day = today.getDay();
      const diff = today.getDate() - day + (day === 0 ? -6 : 1); // Pazartesi gününü bul
      firstDay.setDate(diff);
      
      this.startDate = this.formatDateForInput(firstDay);
      this.endDate = this.formatDateForInput(today);
      
      this.applyCustomDateRange();
      
      logger.debug('Bu hafta filtresi uygulandı');
    },
    
    // Input için tarih formatla (YYYY-MM-DD)
    formatDateForInput(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      
      return `${year}-${month}-${day}`;
    },
    
    // Gösterilecek tarih formatı (DD/MM/YYYY)
    formatDateForDisplay(dateStr) {
      if (!dateStr) return '';
      
      try {
        const date = new Date(dateStr);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        return `${day}/${month}/${year}`;
      } catch (e) {
        logger.error(`Tarih formatı hatası: ${e.message}`);
        return dateStr;
      }
    }
  };
}

// ES modül olarak dışa aktar
export default dateFilterComponent;