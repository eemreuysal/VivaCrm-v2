// VivaCRM - Security Helper Functions
export const security = {
    // Sanitize HTML to prevent XSS
    sanitizeHtml(html) {
        const tempDiv = document.createElement('div');
        tempDiv.textContent = html;
        return tempDiv.innerHTML;
    },

    // Create trusted HTML element
    createSafeElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);

        // Set attributes safely
        for (const [key, value] of Object.entries(attributes)) {
            if (key === 'className') {
                element.className = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else if (['id', 'title', 'alt', 'placeholder'].includes(key)) {
                element[key] = value;
            }
        }

        // Set content safely
        if (content) {
            element.textContent = content;
        }

        return element;
    },

    // Validate URL to prevent XSS
    isValidUrl(string) {
        try {
            const url = new URL(string);
            return ['http:', 'https:', 'mailto:'].includes(url.protocol);
        } catch {
            return false;
        }
    },

    // Safe JSON parse
    safeJsonParse(json, fallback = null) {
        try {
            return JSON.parse(json);
        } catch {
            console.warn('Invalid JSON:', json);
            return fallback;
        }
    },

    // Generate nonce for inline scripts
    generateNonce() {
        const array = new Uint8Array(16);
        window.crypto.getRandomValues(array);
        return btoa(String.fromCharCode.apply(null, array));
    },

    // Content Security Policy builder
    buildCSP(directives = {}) {
        const defaultDirectives = {
            'default-src': ['\'self\''],
            'script-src': ['\'self\'', '\'unsafe-inline\'', '\'unsafe-eval\''],
            'style-src': ['\'self\'', '\'unsafe-inline\''],
            'img-src': ['\'self\'', 'data:', 'https:'],
            'font-src': ['\'self\''],
            'connect-src': ['\'self\''],
            'frame-src': ['\'none\''],
            'object-src': ['\'none\''],
            'base-uri': ['\'self\''],
            'form-action': ['\'self\'']
        };

        const merged = { ...defaultDirectives, ...directives };

        return Object.entries(merged)
            .map(([directive, sources]) => `${directive} ${sources.join(' ')}`)
            .join('; ');
    },

    // Set CSP header via meta tag
    setCSP(directives = {}) {
        const csp = this.buildCSP(directives);
        const meta = document.createElement('meta');
        meta.httpEquiv = 'Content-Security-Policy';
        meta.content = csp;
        document.head.appendChild(meta);
    }
};

export default security;
