/**
 * Kart bileşeni - Alpine.js component
 * 
 * VivaCRM projesinde içerik kartları görüntülemek için kullanılır.
 * Katlanabilir modda kullanım için gerekli davranışları ekler.
 */
export default function card() {
  return {
    // Başlangıç durumu, props'tan gelecek
    collapsed: false,
    
    /**
     * İçeriği aç/kapat
     */
    toggle() {
      this.collapsed = !this.collapsed;
      
      // Durum değişikliğini event olarak bildir
      this.$dispatch('card-toggle', {
        id: this.$el.id,
        collapsed: this.collapsed
      });
    },
    
    /**
     * Başlatma fonksiyonu
     * @param {boolean} initialCollapsed - Başlangıç durumu
     */
    init(initialCollapsed = false) {
      // Başlangıç durumunu atama
      this.collapsed = initialCollapsed;
      
      // Hash'te id varsa otomatik aç
      if (window.location.hash === `#${this.$el.id}`) {
        this.collapsed = false;
        
        // Görünür olması için scroll
        setTimeout(() => {
          this.$el.scrollIntoView({ behavior: 'smooth' });
        }, 200);
      }
    }
  }
}