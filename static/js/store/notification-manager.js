/**
 * Notification Manager - Bildirim yönetimi
 */
export class NotificationManager {
    constructor() {
        this.notifications = [];
        this.listeners = [];
    }

    /**
     * Bildirim ekle
     */
    add(notification) {
        const id = Date.now();
        const newNotification = {
            id,
            type: 'info',
            duration: 5000,
            ...notification,
            timestamp: new Date().toISOString()
        };

        this.notifications.push(newNotification);
        this.notifyListeners(newNotification);

        // Auto-remove after duration
        if (newNotification.duration > 0) {
            setTimeout(() => this.remove(id), newNotification.duration);
        }

        return id;
    }

    /**
     * Bildirim kaldır
     */
    remove(id) {
        const index = this.notifications.findIndex((n) => n.id === id);
        if (index !== -1) {
            this.notifications.splice(index, 1);
            this.notifyListeners({ id, removed: true });
        }
    }

    /**
     * Dinleyici ekle
     */
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter((l) => l !== callback);
        };
    }

    /**
     * Dinleyicileri bilgilendir
     */
    notifyListeners(notification) {
        this.listeners.forEach((callback) => callback(notification));
    }
}
