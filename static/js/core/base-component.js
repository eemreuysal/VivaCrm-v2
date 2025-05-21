// VivaCRM - Base Component Class for Memory Management
export class BaseComponent {
    constructor() {
        this.eventListeners = [];
        this.subscriptions = [];
        this.timers = [];
        this.observers = [];
        this.abortControllers = [];
    }

    /**
     * Add event listener with automatic cleanup
     */
    addEventListener(element, event, handler, options = {}) {
        if (!element) return;

        element.addEventListener(event, handler, options);
        this.eventListeners.push({ element, event, handler, options });
    }

    /**
     * Subscribe to store with automatic cleanup
     */
    subscribe(key, callback) {
        const unsubscribe = window.vivaCRM?.store?.subscribe(key, callback);
        if (unsubscribe) {
            this.subscriptions.push(unsubscribe);
        }
        return unsubscribe;
    }

    /**
     * Set timeout with automatic cleanup
     */
    setTimeout(callback, delay) {
        const timer = setTimeout(callback, delay);
        this.timers.push(timer);
        return timer;
    }

    /**
     * Set interval with automatic cleanup
     */
    setInterval(callback, delay) {
        const timer = setInterval(callback, delay);
        this.timers.push(timer);
        return timer;
    }

    /**
     * Create MutationObserver with automatic cleanup
     */
    observe(element, callback, options) {
        if (!element) return;

        const observer = new MutationObserver(callback);
        observer.observe(element, options);
        this.observers.push(observer);
        return observer;
    }

    /**
     * Create AbortController for fetch requests
     */
    createAbortController() {
        const controller = new AbortController();
        this.abortControllers.push(controller);
        return controller;
    }

    /**
     * Clean up all resources
     */
    destroy() {
        // Remove event listeners
        this.eventListeners.forEach(({ element, event, handler, options }) => {
            element?.removeEventListener(event, handler, options);
        });
        this.eventListeners = [];

        // Unsubscribe from store
        this.subscriptions.forEach((unsubscribe) => {
            if (typeof unsubscribe === 'function') {
                unsubscribe();
            }
        });
        this.subscriptions = [];

        // Clear timers
        this.timers.forEach((timer) => {
            clearTimeout(timer);
            clearInterval(timer);
        });
        this.timers = [];

        // Disconnect observers
        this.observers.forEach((observer) => {
            observer.disconnect();
        });
        this.observers = [];

        // Abort pending requests
        this.abortControllers.forEach((controller) => {
            if (!controller.signal.aborted) {
                controller.abort();
            }
        });
        this.abortControllers = [];
    }
}

/**
 * Alpine.js Component Mixin
 */
export function createAlpineComponent(componentDefinition) {
    const baseComponent = new BaseComponent();

    return {
        ...componentDefinition,

        init() {
            // Call original init if exists
            if (componentDefinition.init) {
                componentDefinition.init.call(this);
            }

            // Set up destroy on Alpine component destroy
            this.$watch('$destroy', () => {
                this.destroy();
            });
        },

        destroy() {
            // Call original destroy if exists
            if (componentDefinition.destroy) {
                componentDefinition.destroy.call(this);
            }

            // Clean up base component
            baseComponent.destroy();
        },

        // Proxy methods to base component
        addEventListener: baseComponent.addEventListener.bind(baseComponent),
        subscribe: baseComponent.subscribe.bind(baseComponent),
        setTimeout: baseComponent.setTimeout.bind(baseComponent),
        setInterval: baseComponent.setInterval.bind(baseComponent),
        observe: baseComponent.observe.bind(baseComponent),
        createAbortController: baseComponent.createAbortController.bind(baseComponent)
    };
}

export default BaseComponent;
