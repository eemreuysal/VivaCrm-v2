// VivaCRM - Search Manager Module

/**
 * Arama işlemlerini yöneten modül
 * Debounce, cache ve abort desteği ile
 * @class SearchManager
 */
export class SearchManager {
    /**
     * @param {Object} options - Konfigürasyon seçenekleri
     * @param {string} options.endpoint - API endpoint URL'i
     * @param {number} [options.debounceDelay=300] - Debounce gecikmesi (ms)
     * @param {number} [options.minLength=2] - Minimum arama karakter sayısı
     * @param {boolean} [options.cache=true] - Cache kullanımı
     * @param {number} [options.cacheTime=300000] - Cache süresi (5 dakika)
     */
    constructor(options = {}) {
        this.endpoint = options.endpoint;
        this.debounceDelay = options.debounceDelay || 300;
        this.minLength = options.minLength || 2;
        this.cache = options.cache !== false;
        this.cacheTime = options.cacheTime || 300000; // 5 dakika

        this.searchCache = new Map();
        this.currentController = null;
        this.debounceTimer = null;
    }

    /**
     * Arama yap
     * @param {string} query - Arama sorgusu
     * @param {Object} [params={}] - Ek parametreler
     * @returns {Promise<Object>} Arama sonuçları
     */
    async search(query, params = {}) {
        // Trim and validate query
        query = query.trim();

        if (query.length < this.minLength) {
            return { results: [], query: query };
        }

        // Check cache first
        const cacheKey = this.getCacheKey(query, params);
        if (this.cache) {
            const cachedResult = this.getFromCache(cacheKey);
            if (cachedResult) {
                return cachedResult;
            }
        }

        // Abort previous request
        if (this.currentController) {
            this.currentController.abort();
        }

        // Create new abort controller
        this.currentController = new AbortController();

        try {
            const response = await fetch(this.buildUrl(query, params), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                signal: this.currentController.signal
            });

            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }

            const data = await response.json();

            // Cache result
            if (this.cache) {
                this.saveToCache(cacheKey, data);
            }

            return data;
        } catch (error) {
            if (error.name === 'AbortError') {
                // Request was aborted, ignore
                return null;
            }
            throw error;
        } finally {
            this.currentController = null;
        }
    }

    /**
     * Debounced search
     * @param {string} query - Arama sorgusu
     * @param {Object} [params={}] - Ek parametreler
     * @returns {Promise<Object>} Arama sonuçları
     */
    debouncedSearch(query, params = {}) {
        return new Promise((resolve, reject) => {
            clearTimeout(this.debounceTimer);

            this.debounceTimer = setTimeout(async () => {
                try {
                    const result = await this.search(query, params);
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            }, this.debounceDelay);
        });
    }

    /**
     * Build URL with query parameters
     * @private
     * @param {string} query - Arama sorgusu
     * @param {Object} params - Parametreler
     * @returns {string} URL
     */
    buildUrl(query, params) {
        const url = new URL(this.endpoint, window.location.origin);
        url.searchParams.append('q', query);

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                url.searchParams.append(key, value);
            }
        });

        return url.toString();
    }

    /**
     * Generate cache key
     * @private
     * @param {string} query - Arama sorgusu
     * @param {Object} params - Parametreler
     * @returns {string} Cache key
     */
    getCacheKey(query, params) {
        return JSON.stringify({ query, params });
    }

    /**
     * Get from cache
     * @private
     * @param {string} key - Cache key
     * @returns {Object|null} Cached data or null
     */
    getFromCache(key) {
        const cached = this.searchCache.get(key);

        if (!cached) return null;

        // Check if cache is expired
        if (Date.now() - cached.timestamp > this.cacheTime) {
            this.searchCache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Save to cache
     * @private
     * @param {string} key - Cache key
     * @param {Object} data - Data to cache
     */
    saveToCache(key, data) {
        this.searchCache.set(key, {
            data: data,
            timestamp: Date.now()
        });

        // Limit cache size
        if (this.searchCache.size > 100) {
            const firstKey = this.searchCache.keys().next().value;
            this.searchCache.delete(firstKey);
        }
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.searchCache.clear();
    }

    /**
     * Cancel current search
     */
    cancel() {
        if (this.currentController) {
            this.currentController.abort();
            this.currentController = null;
        }

        clearTimeout(this.debounceTimer);
    }
}

/**
 * Alpine.js magic helper for search
 */
if (window.Alpine) {
    Alpine.magic('search', () => {
        return (endpoint, options = {}) => {
            return new SearchManager({ endpoint, ...options });
        };
    });
}

export default SearchManager;
