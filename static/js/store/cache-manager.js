/**
 * Cache Manager - Önbellek yönetimi
 */
export class CacheManager {
    constructor() {
        this.cache = new Map();
        this.ttl = 5 * 60 * 1000; // 5 dakika default TTL
    }

    /**
     * Cache'e veri ekle
     */
    set(key, value, ttl = this.ttl) {
        const expiry = ttl ? Date.now() + ttl : null;
        this.cache.set(key, { value, expiry });
    }

    /**
     * Cache'den veri oku
     */
    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        if (item.expiry && Date.now() > item.expiry) {
            this.cache.delete(key);
            return null;
        }

        return item.value;
    }

    /**
     * Cache'i temizle
     */
    clear() {
        this.cache.clear();
    }
}
