// VivaCRM - Virtual Scrolling Module

/**
 * Virtual scrolling implementasyonu
 * Büyük listeler için performans optimizasyonu sağlar
 * @class VirtualScroll
 */
export class VirtualScroll {
    /**
     * @param {Object} options - Konfigürasyon seçenekleri
     * @param {HTMLElement} options.container - Scroll container
     * @param {number} options.itemHeight - Her item'ın yüksekliği
     * @param {number} options.bufferSize - Buffer zone büyüklüğü
     * @param {Function} options.renderItem - Item render fonksiyonu
     * @param {Array} options.data - Veri listesi
     */
    constructor(options) {
        this.container = options.container;
        this.itemHeight = options.itemHeight;
        this.bufferSize = options.bufferSize || 5;
        this.renderItem = options.renderItem;
        this.data = options.data || [];

        this.scrollTop = 0;
        this.containerHeight = 0;
        this.totalHeight = 0;
        this.visibleStart = 0;
        this.visibleEnd = 0;

        this.init();
    }

    /**
     * Virtual scroll'u başlat
     */
    init() {
        this.containerHeight = this.container.clientHeight;
        this.totalHeight = this.data.length * this.itemHeight;

        // Create wrapper elements
        this.viewport = document.createElement('div');
        this.viewport.className = 'virtual-scroll-viewport';
        this.viewport.style.height = `${this.totalHeight}px`;

        this.content = document.createElement('div');
        this.content.className = 'virtual-scroll-content';

        // Move existing content
        while (this.container.firstChild) {
            this.container.removeChild(this.container.firstChild);
        }

        this.viewport.appendChild(this.content);
        this.container.appendChild(this.viewport);

        // Setup event listeners
        this.container.addEventListener('scroll', this.onScroll.bind(this));

        // Initial render
        this.render();
    }

    /**
     * Scroll event handler
     * @param {Event} event - Scroll event
     */
    onScroll(event) {
        this.scrollTop = event.target.scrollTop;
        this.render();
    }

    /**
     * Görünür item'ları hesapla ve render et
     */
    render() {
        const scrollTop = this.scrollTop;
        const visibleStart = Math.floor(scrollTop / this.itemHeight);
        const visibleEnd = Math.ceil((scrollTop + this.containerHeight) / this.itemHeight);

        // Buffer ekle
        const renderStart = Math.max(0, visibleStart - this.bufferSize);
        const renderEnd = Math.min(this.data.length, visibleEnd + this.bufferSize);

        // Only re-render if the visible range has changed
        if (renderStart === this.visibleStart && renderEnd === this.visibleEnd) {
            return;
        }

        this.visibleStart = renderStart;
        this.visibleEnd = renderEnd;

        // Clear content safely
        while (this.content.firstChild) {
            this.content.removeChild(this.content.firstChild);
        }

        // Position content
        this.content.style.transform = `translateY(${renderStart * this.itemHeight}px)`;

        // Render visible items
        for (let i = renderStart; i < renderEnd; i++) {
            const item = this.data[i];
            const element = this.renderItem(item, i);
            element.style.height = `${this.itemHeight}px`;
            this.content.appendChild(element);
        }
    }

    /**
     * Veri setini güncelle
     * @param {Array} data - Yeni veri listesi
     */
    updateData(data) {
        this.data = data;
        this.totalHeight = this.data.length * this.itemHeight;
        this.viewport.style.height = `${this.totalHeight}px`;
        this.render();
    }

    /**
     * Belirli bir index'e scroll et
     * @param {number} index - Item index
     */
    scrollToIndex(index) {
        const scrollTop = index * this.itemHeight;
        this.container.scrollTop = scrollTop;
    }

    /**
     * Cleanup
     */
    destroy() {
        this.container.removeEventListener('scroll', this.onScroll.bind(this));
        while (this.container.firstChild) {
            this.container.removeChild(this.container.firstChild);
        }
    }
}

/**
 * Alpine.js directive for virtual scrolling
 */
if (window.Alpine) {
    Alpine.directive('virtual-scroll', (el, { expression }, { evaluate }) => {
        const options = evaluate(expression);

        const virtualScroll = new VirtualScroll({
            container: el,
            ...options
        });

        // Store instance for cleanup
        el._virtualScroll = virtualScroll;

        // Cleanup on destroy
        el._x_cleanups = el._x_cleanups || [];
        el._x_cleanups.push(() => {
            virtualScroll.destroy();
        });
    });
}

export default VirtualScroll;
