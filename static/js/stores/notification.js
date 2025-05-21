/**
 * Notification Store
 *
 * VivaCRM için bildirim yönetimi
 * @module stores/notification
 */

/**
 * Bildirimleri yönetme için Alpine.js store
 * @returns {Object} Alpine.js store
 */
export default {
    // State
    notifications: [],
    counter: 0,

    /**
   * Store başlatma
   */
    init() {
        console.info('Notification store initialized');
    },

    /**
   * Yeni bildirim ekle
   * @param {Object} notification - Bildirim nesnesi
   * @param {string} notification.type - Bildirim tipi: 'info', 'success', 'warning', 'error'
   * @param {string} notification.message - Bildirim mesajı
   * @param {number} [notification.timeout=5000] - Otomatik kapatma süresi (ms)
   * @param {boolean} [notification.closable=true] - Kapatılabilir mi?
   */
    add({ type = 'info', message, timeout = 5000, closable = true }) {
        const id = `notification-${Date.now()}-${this.counter++}`;

        const notification = {
            id,
            type,
            message,
            closable,
            createdAt: new Date()
        };

        this.notifications.push(notification);

        // Otomatik kapatma süresi tanımlanmışsa, bildirim için zamanlayıcı başlat
        if (timeout > 0) {
            setTimeout(() => {
                this.remove(id);
            }, timeout);
        }

        // Özel olay tetikle
        document.dispatchEvent(new CustomEvent('vivacrm:notification-added', {
            detail: { notification }
        }));

        return id;
    },

    /**
   * Bildirim kaldır
   * @param {string} id - Bildirim ID
   */
    remove(id) {
        const index = this.notifications.findIndex((n) => n.id === id);
        if (index !== -1) {
            const notification = this.notifications[index];
            this.notifications.splice(index, 1);

            // Özel olay tetikle
            document.dispatchEvent(new CustomEvent('vivacrm:notification-removed', {
                detail: { notification }
            }));
        }
    },

    /**
   * Tüm bildirimleri temizle
   */
    clear() {
        this.notifications = [];

        // Özel olay tetikle
        document.dispatchEvent(new CustomEvent('vivacrm:notifications-cleared'));
    },

    /**
   * Başarı bildirimi ekle (helper)
   * @param {string} message - Bildirim mesajı
   * @param {number} [timeout=5000] - Otomatik kapatma süresi (ms)
   */
    success(message, timeout = 5000) {
        return this.add({ type: 'success', message, timeout });
    },

    /**
   * Hata bildirimi ekle (helper)
   * @param {string} message - Bildirim mesajı
   * @param {number} [timeout=0] - Otomatik kapatma süresi (ms), varsayılan olarak otomatik kapanmaz
   */
    error(message, timeout = 0) {
        return this.add({ type: 'error', message, timeout });
    },

    /**
   * Bilgi bildirimi ekle (helper)
   * @param {string} message - Bildirim mesajı
   * @param {number} [timeout=5000] - Otomatik kapatma süresi (ms)
   */
    info(message, timeout = 5000) {
        return this.add({ type: 'info', message, timeout });
    },

    /**
   * Uyarı bildirimi ekle (helper)
   * @param {string} message - Bildirim mesajı
   * @param {number} [timeout=8000] - Otomatik kapatma süresi (ms)
   */
    warning(message, timeout = 8000) {
        return this.add({ type: 'warning', message, timeout });
    }
};
