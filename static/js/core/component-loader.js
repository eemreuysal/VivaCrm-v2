/**
 * Component Loader
 * Modern component loading with lazy loading support
 */
export class ComponentLoader {
    constructor() {
        this.loadedComponents = new Set();
        this.componentCache = new Map();
    }

    /**
     * Lazy load a component
     * @param {string} name - Component name
     * @returns {Promise<any>} - Component module
     */
    async loadComponent(name) {
        // Check cache first
        if (this.componentCache.has(name)) {
            return this.componentCache.get(name);
        }

        // Check if already loaded
        if (this.loadedComponents.has(name)) {
            return null;
        }

        try {
            const module = await import(`../components/${name}.js`);
            this.loadedComponents.add(name);
            this.componentCache.set(name, module);

            if (module.default && typeof module.default.init === 'function') {
                module.default.init();
            }

            return module;
        } catch (error) {
            console.error(`Failed to load component: ${name}`, error);
            return null;
        }
    }

    /**
     * Load multiple components
     * @param {string[]} components - Array of component names
     * @returns {Promise<void>}
     */
    async loadComponents(components) {
        const promises = components.map((name) => this.loadComponent(name));
        await Promise.all(promises);
    }

    /**
     * Load component based on route or condition
     * @param {string} route - Current route
     * @returns {Promise<void>}
     */
    async loadRouteComponents(route) {
        const routeComponents = {
            '/dashboard/': ['dashboard', 'charts'],
            '/orders/': ['orders', 'forms'],
            '/customers/': ['customers', 'forms'],
            '/products/': ['products', 'forms']
        };

        const componentsToLoad = routeComponents[route] || [];
        await this.loadComponents(componentsToLoad);
    }

    /**
     * Check if component is loaded
     * @param {string} name - Component name
     * @returns {boolean}
     */
    isLoaded(name) {
        return this.loadedComponents.has(name);
    }

    /**
     * Clear component cache
     */
    clearCache() {
        this.componentCache.clear();
    }
}

// Export singleton instance
export const componentLoader = new ComponentLoader();
