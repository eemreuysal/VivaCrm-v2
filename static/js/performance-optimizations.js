/**
 * VivaCRM v2 Frontend Performans Optimizasyonları
 * 
 * Bu dosya, frontend tarafında yapılacak performans iyileştirmelerini içerir.
 */

// 1. Lazy Loading Implementation
class LazyLoader {
    constructor() {
        this.imageObserver = null;
        this.componentObserver = null;
        this.init();
    }

    init() {
        // Image lazy loading
        this.setupImageLazyLoading();
        
        // Component lazy loading
        this.setupComponentLazyLoading();
        
        // Intersection Observer for infinite scroll
        this.setupInfiniteScroll();
    }

    setupImageLazyLoading() {
        const imageOptions = {
            root: null,
            rootMargin: '50px 0px',
            threshold: 0.01
        };

        this.imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // Load the image
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        img.classList.add('loaded');
                        
                        // Stop observing this image
                        observer.unobserve(img);
                    }
                }
            });
        }, imageOptions);

        // Start observing lazy images
        document.querySelectorAll('img.lazy').forEach(img => {
            this.imageObserver.observe(img);
        });
    }

    setupComponentLazyLoading() {
        const componentOptions = {
            root: null,
            rootMargin: '100px 0px',
            threshold: 0.01
        };

        this.componentObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const component = entry.target;
                    const componentUrl = component.dataset.component;
                    
                    // Load component dynamically
                    this.loadComponent(componentUrl, component);
                    
                    // Stop observing
                    observer.unobserve(component);
                }
            });
        }, componentOptions);

        // Start observing lazy components
        document.querySelectorAll('[data-lazy-component]').forEach(component => {
            this.componentObserver.observe(component);
        });
    }

    async loadComponent(url, container) {
        try {
            const response = await fetch(url);
            const html = await response.text();
            container.innerHTML = html;
            
            // Trigger Alpine.js refresh if needed
            if (window.Alpine) {
                Alpine.initialize(container);
            }
        } catch (error) {
            console.error('Failed to load component:', error);
        }
    }

    setupInfiniteScroll() {
        const scrollTrigger = document.querySelector('[data-infinite-scroll]');
        if (!scrollTrigger) return;

        const scrollOptions = {
            root: null,
            rootMargin: '100px',
            threshold: 0.01
        };

        const scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Load more content
                    this.loadMoreContent(entry.target);
                }
            });
        }, scrollOptions);

        scrollObserver.observe(scrollTrigger);
    }

    async loadMoreContent(trigger) {
        const url = trigger.dataset.nextUrl;
        if (!url || trigger.dataset.loading === 'true') return;

        trigger.dataset.loading = 'true';

        try {
            const response = await fetch(url);
            const data = await response.json();
            
            // Append new content
            const container = document.querySelector(trigger.dataset.container);
            container.insertAdjacentHTML('beforeend', data.html);
            
            // Update next URL
            trigger.dataset.nextUrl = data.nextUrl;
            
            // Re-initialize any dynamic content
            this.reinitializeDynamicContent(container);
        } catch (error) {
            console.error('Failed to load more content:', error);
        } finally {
            trigger.dataset.loading = 'false';
        }
    }

    reinitializeDynamicContent(container) {
        // Re-observe new lazy images
        container.querySelectorAll('img.lazy').forEach(img => {
            this.imageObserver.observe(img);
        });

        // Re-initialize Alpine components
        if (window.Alpine) {
            Alpine.initialize(container);
        }

        // Re-initialize HTMX
        if (window.htmx) {
            htmx.process(container);
        }
    }
}

// 2. Request Debouncing and Throttling
class RequestOptimizer {
    constructor() {
        this.debounceTimers = {};
        this.throttleTimers = {};
        this.cache = new Map();
    }

    debounce(func, delay, key) {
        return (...args) => {
            clearTimeout(this.debounceTimers[key]);
            this.debounceTimers[key] = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    }

    throttle(func, limit, key) {
        return (...args) => {
            if (this.throttleTimers[key]) return;
            
            func.apply(this, args);
            this.throttleTimers[key] = true;
            
            setTimeout(() => {
                this.throttleTimers[key] = false;
            }, limit);
        };
    }

    async cachedFetch(url, options = {}, ttl = 300000) { // 5 minutes default
        const cacheKey = `${url}:${JSON.stringify(options)}`;
        
        // Check cache
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < ttl) {
                return cached.data;
            }
        }

        // Fetch and cache
        const response = await fetch(url, options);
        const data = await response.json();
        
        this.cache.set(cacheKey, {
            data: data,
            timestamp: Date.now()
        });

        // Cleanup old cache entries
        this.cleanupCache();

        return data;
    }

    cleanupCache() {
        if (this.cache.size > 100) {
            // Remove oldest entries
            const entries = Array.from(this.cache.entries());
            entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
            
            for (let i = 0; i < 20; i++) {
                this.cache.delete(entries[i][0]);
            }
        }
    }
}

// 3. Virtual Scrolling for Large Lists
class VirtualScroller {
    constructor(container, options = {}) {
        this.container = container;
        this.itemHeight = options.itemHeight || 50;
        this.buffer = options.buffer || 5;
        this.items = [];
        this.visibleRange = { start: 0, end: 0 };
        
        this.init();
    }

    init() {
        // Create viewport
        this.viewport = document.createElement('div');
        this.viewport.className = 'virtual-scroll-viewport';
        this.viewport.style.height = '100%';
        this.viewport.style.overflow = 'auto';
        
        // Create content container
        this.content = document.createElement('div');
        this.content.className = 'virtual-scroll-content';
        
        this.viewport.appendChild(this.content);
        this.container.appendChild(this.viewport);
        
        // Setup scroll listener
        this.viewport.addEventListener('scroll', this.handleScroll.bind(this));
    }

    setItems(items) {
        this.items = items;
        this.updateContent();
    }

    handleScroll() {
        const scrollTop = this.viewport.scrollTop;
        const viewportHeight = this.viewport.clientHeight;
        
        // Calculate visible range
        const startIndex = Math.max(0, Math.floor(scrollTop / this.itemHeight) - this.buffer);
        const endIndex = Math.min(
            this.items.length,
            Math.ceil((scrollTop + viewportHeight) / this.itemHeight) + this.buffer
        );
        
        if (startIndex !== this.visibleRange.start || endIndex !== this.visibleRange.end) {
            this.visibleRange = { start: startIndex, end: endIndex };
            this.updateVisibleItems();
        }
    }

    updateContent() {
        // Set total height
        const totalHeight = this.items.length * this.itemHeight;
        this.content.style.height = `${totalHeight}px`;
        
        // Initial render
        this.handleScroll();
    }

    updateVisibleItems() {
        // Clear current content
        this.content.innerHTML = '';
        
        // Create spacer for items above
        const spacerTop = document.createElement('div');
        spacerTop.style.height = `${this.visibleRange.start * this.itemHeight}px`;
        this.content.appendChild(spacerTop);
        
        // Render visible items
        for (let i = this.visibleRange.start; i < this.visibleRange.end; i++) {
            const itemElement = this.renderItem(this.items[i], i);
            this.content.appendChild(itemElement);
        }
        
        // Create spacer for items below
        const spacerBottom = document.createElement('div');
        const bottomHeight = (this.items.length - this.visibleRange.end) * this.itemHeight;
        spacerBottom.style.height = `${bottomHeight}px`;
        this.content.appendChild(spacerBottom);
    }

    renderItem(item, index) {
        const element = document.createElement('div');
        element.className = 'virtual-scroll-item';
        element.style.height = `${this.itemHeight}px`;
        element.innerHTML = this.options.renderItem ? this.options.renderItem(item, index) : item.toString();
        return element;
    }
}

// 4. Web Worker for Heavy Computations
class ComputationWorker {
    constructor() {
        this.worker = null;
        this.init();
    }

    init() {
        // Create worker script as blob
        const workerScript = `
            self.addEventListener('message', function(e) {
                const { type, data } = e.data;
                
                switch(type) {
                    case 'sort':
                        const sorted = performSort(data);
                        self.postMessage({ type: 'sorted', data: sorted });
                        break;
                        
                    case 'filter':
                        const filtered = performFilter(data);
                        self.postMessage({ type: 'filtered', data: filtered });
                        break;
                        
                    case 'aggregate':
                        const aggregated = performAggregation(data);
                        self.postMessage({ type: 'aggregated', data: aggregated });
                        break;
                }
            });
            
            function performSort(data) {
                return data.items.sort((a, b) => {
                    const aVal = a[data.sortBy];
                    const bVal = b[data.sortBy];
                    return data.order === 'asc' ? aVal - bVal : bVal - aVal;
                });
            }
            
            function performFilter(data) {
                return data.items.filter(item => {
                    return data.filters.every(filter => {
                        const value = item[filter.field];
                        switch(filter.operator) {
                            case 'equals':
                                return value === filter.value;
                            case 'contains':
                                return value.includes(filter.value);
                            case 'greater':
                                return value > filter.value;
                            case 'less':
                                return value < filter.value;
                            default:
                                return true;
                        }
                    });
                });
            }
            
            function performAggregation(data) {
                return data.items.reduce((acc, item) => {
                    const key = item[data.groupBy];
                    if (!acc[key]) {
                        acc[key] = { count: 0, sum: 0, items: [] };
                    }
                    acc[key].count++;
                    acc[key].sum += item[data.sumField] || 0;
                    acc[key].items.push(item);
                    return acc;
                }, {});
            }
        `;

        const blob = new Blob([workerScript], { type: 'application/javascript' });
        this.worker = new Worker(URL.createObjectURL(blob));
    }

    sort(items, sortBy, order = 'asc') {
        return new Promise((resolve) => {
            this.worker.onmessage = (e) => {
                if (e.data.type === 'sorted') {
                    resolve(e.data.data);
                }
            };
            
            this.worker.postMessage({
                type: 'sort',
                data: { items, sortBy, order }
            });
        });
    }

    filter(items, filters) {
        return new Promise((resolve) => {
            this.worker.onmessage = (e) => {
                if (e.data.type === 'filtered') {
                    resolve(e.data.data);
                }
            };
            
            this.worker.postMessage({
                type: 'filter',
                data: { items, filters }
            });
        });
    }

    aggregate(items, groupBy, sumField) {
        return new Promise((resolve) => {
            this.worker.onmessage = (e) => {
                if (e.data.type === 'aggregated') {
                    resolve(e.data.data);
                }
            };
            
            this.worker.postMessage({
                type: 'aggregate',
                data: { items, groupBy, sumField }
            });
        });
    }

    terminate() {
        if (this.worker) {
            this.worker.terminate();
        }
    }
}

// 5. Resource Prefetching
class ResourcePrefetcher {
    constructor() {
        this.prefetchedUrls = new Set();
        this.init();
    }

    init() {
        // Prefetch on link hover
        document.addEventListener('mouseover', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.shouldPrefetch(link)) {
                this.prefetchUrl(link.href);
            }
        });

        // Prefetch visible links
        this.prefetchVisibleLinks();
    }

    shouldPrefetch(link) {
        // Don't prefetch external links
        if (link.host !== window.location.host) return false;
        
        // Don't prefetch downloads
        if (link.hasAttribute('download')) return false;
        
        // Don't prefetch already prefetched URLs
        if (this.prefetchedUrls.has(link.href)) return false;
        
        // Don't prefetch certain file types
        const excludedExtensions = ['.pdf', '.zip', '.exe', '.dmg'];
        if (excludedExtensions.some(ext => link.href.endsWith(ext))) return false;
        
        return true;
    }

    prefetchUrl(url) {
        if (this.prefetchedUrls.has(url)) return;
        
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        link.as = 'document';
        
        document.head.appendChild(link);
        this.prefetchedUrls.add(url);
    }

    prefetchVisibleLinks() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const link = entry.target;
                    if (this.shouldPrefetch(link)) {
                        this.prefetchUrl(link.href);
                    }
                }
            });
        }, {
            rootMargin: '100px'
        });

        // Observe all links
        document.querySelectorAll('a[href]').forEach(link => {
            observer.observe(link);
        });
    }

    // Prefetch API data
    prefetchApiData(endpoint, options = {}) {
        fetch(endpoint, {
            ...options,
            priority: 'low'
        }).then(response => response.json()).then(data => {
            // Store in session storage for quick access
            sessionStorage.setItem(`prefetch:${endpoint}`, JSON.stringify({
                data: data,
                timestamp: Date.now()
            }));
        }).catch(err => {
            console.warn('Prefetch failed:', err);
        });
    }
}

// 6. Performance Monitor
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.observers = {};
        this.init();
    }

    init() {
        // Monitor page load performance
        this.monitorPageLoad();
        
        // Monitor runtime performance
        this.monitorRuntime();
        
        // Monitor resource loading
        this.monitorResources();
        
        // Setup performance observer
        this.setupPerformanceObserver();
    }

    monitorPageLoad() {
        window.addEventListener('load', () => {
            const perfData = performance.getEntriesByType('navigation')[0];
            
            this.metrics.pageLoad = {
                domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                domInteractive: perfData.domInteractive,
                firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime,
                firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
            };
            
            // Send metrics to analytics
            this.sendMetrics('pageLoad', this.metrics.pageLoad);
        });
    }

    monitorRuntime() {
        // Monitor long tasks
        if ('PerformanceObserver' in window) {
            this.observers.longTask = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.metrics.longTasks = this.metrics.longTasks || [];
                    this.metrics.longTasks.push({
                        name: entry.name,
                        duration: entry.duration,
                        startTime: entry.startTime
                    });
                    
                    // Log long tasks over 50ms
                    if (entry.duration > 50) {
                        console.warn('Long task detected:', entry);
                    }
                }
            });

            this.observers.longTask.observe({ entryTypes: ['longtask'] });
        }
    }

    monitorResources() {
        // Monitor resource loading
        if ('PerformanceObserver' in window) {
            this.observers.resource = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    // Track slow resources
                    if (entry.duration > 1000) {
                        console.warn('Slow resource:', entry.name, entry.duration);
                    }
                    
                    // Categorize resources
                    const resourceType = entry.initiatorType;
                    this.metrics.resources = this.metrics.resources || {};
                    this.metrics.resources[resourceType] = this.metrics.resources[resourceType] || [];
                    this.metrics.resources[resourceType].push({
                        name: entry.name,
                        duration: entry.duration,
                        size: entry.transferSize
                    });
                }
            });

            this.observers.resource.observe({ entryTypes: ['resource'] });
        }
    }

    setupPerformanceObserver() {
        // Layout shift
        if ('PerformanceObserver' in window && 'LayoutShift' in window) {
            this.observers.layoutShift = new PerformanceObserver((list) => {
                let cls = 0;
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        cls += entry.value;
                    }
                }
                this.metrics.cls = cls;
            });

            this.observers.layoutShift.observe({ entryTypes: ['layout-shift'] });
        }

        // Largest contentful paint
        if ('PerformanceObserver' in window && 'LargestContentfulPaint' in window) {
            this.observers.lcp = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.lcp = lastEntry.renderTime || lastEntry.loadTime;
            });

            this.observers.lcp.observe({ entryTypes: ['largest-contentful-paint'] });
        }

        // First input delay
        if ('PerformanceObserver' in window && 'PerformanceEventTiming' in window) {
            this.observers.fid = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.metrics.fid = entry.processingStart - entry.startTime;
                    break; // Only need first input
                }
            });

            this.observers.fid.observe({ entryTypes: ['first-input'] });
        }
    }

    sendMetrics(category, data) {
        // Send to analytics endpoint
        if (navigator.sendBeacon) {
            navigator.sendBeacon('/api/analytics/performance', JSON.stringify({
                category: category,
                data: data,
                timestamp: Date.now(),
                url: window.location.href,
                userAgent: navigator.userAgent
            }));
        }
    }

    getMetrics() {
        return this.metrics;
    }

    clearMetrics() {
        this.metrics = {};
    }
}

// Initialize all performance optimizations
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize in production
    if (window.location.hostname !== 'localhost') {
        window.vivacrm = window.vivacrm || {};
        
        // Initialize performance modules
        window.vivacrm.lazyLoader = new LazyLoader();
        window.vivacrm.requestOptimizer = new RequestOptimizer();
        window.vivacrm.resourcePrefetcher = new ResourcePrefetcher();
        window.vivacrm.performanceMonitor = new PerformanceMonitor();
        
        // Initialize virtual scroller for large lists
        const largeListContainers = document.querySelectorAll('[data-virtual-scroll]');
        largeListContainers.forEach(container => {
            const itemHeight = parseInt(container.dataset.itemHeight) || 50;
            const scroller = new VirtualScroller(container, {
                itemHeight: itemHeight,
                renderItem: (item, index) => {
                    // Custom render function
                    return `<div class="list-item">${item.name}</div>`;
                }
            });
            
            // Store reference
            container.virtualScroller = scroller;
        });
        
        // Initialize computation worker for heavy operations
        window.vivacrm.computationWorker = new ComputationWorker();
        
        // Set up request optimizations
        const searchInput = document.querySelector('[data-search]');
        if (searchInput) {
            searchInput.addEventListener('input', 
                window.vivacrm.requestOptimizer.debounce((e) => {
                    // Perform search
                    performSearch(e.target.value);
                }, 300, 'search')
            );
        }
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.vivacrm?.computationWorker) {
        window.vivacrm.computationWorker.terminate();
    }
});