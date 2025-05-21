/**
 * Modal bileşeni - Alpine.js component
 * 
 * VivaCRM projesinde açılır pencere görüntülemek için kullanılır.
 * Bu merkezi bileşen, tüm modal davranışlarını standartlaştırır.
 */
export default function modal() {
  return {
    open: false,
    
    /**
     * Callback fonksiyonunu ayarlar
     * @param {string} id - Modal ID'si
     * @param {Function|null} callback - Onay butonuna tıklandığında çalışacak fonksiyon
     */
    setupCallback(id, callback) {
      if (callback) {
        window[`${id}_confirm`] = callback;
      }
    },
    
    /**
     * Onay butonuna tıklandığında çalışır
     */
    onConfirm() {
      const confirmFunction = window[`${this.$el.id}_confirm`];
      if (typeof confirmFunction === 'function') {
        confirmFunction();
      }
      this.open = false;
    },
    
    /**
     * Bileşen başladığında çalışır
     */
    init() {
      // Escape tuşu ile kapatma dışarıda hallediliyor
      
      // Modal açıldığında body scroll'u engelle
      this.$watch('open', value => {
        if (value) {
          document.body.classList.add('overflow-hidden');
        } else {
          document.body.classList.remove('overflow-hidden');
        }
      });
      
      // Modal dışına tıklayarak kapatma özelliği bu şablonda hallediliyor
    }
  }
}