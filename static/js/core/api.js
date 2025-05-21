// VivaCRM - API Helper Functions
import { utils } from './utils.js';

export class VivaCRMAPI {
    constructor() {
        this.baseURL = '/api/';
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    // Get CSRF token
    getCsrfToken() {
        return utils.getCookie('csrftoken') ||
               document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               window.VivaCRM?.csrfToken || '';
    }

    // Prepare headers
    prepareHeaders(customHeaders = {}) {
        return {
            ...this.headers,
            'X-CSRFToken': this.getCsrfToken(),
            ...customHeaders
        };
    }

    // Handle response
    async handleResponse(response) {
        // Check if response is ok
        if (!response.ok) {
            const error = await this.parseError(response);
            throw error;
        }

        // Parse JSON if content type is JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        }

        return response.text();
    }

    // Parse error response
    async parseError(response) {
        let errorMessage = 'Bir hata oluştu';
        let errorData = {};

        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                errorData = await response.json();
                errorMessage = errorData.message || errorData.error || errorMessage;
            }
        } catch (e) {
            // Not JSON or parsing failed
        }

        // Status based error messages
        if (response.status === 403) {
            errorMessage = errorData.message || 'Bu işlem için yetkiniz yok';
        } else if (response.status === 404) {
            errorMessage = errorData.message || 'Kaynak bulunamadı';
        } else if (response.status >= 500) {
            errorMessage = errorData.message || 'Sunucu hatası';
        }

        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = errorData;
        return error;
    }

    // GET request
    async get(endpoint, params = {}) {
        const url = new URL(this.baseURL + endpoint, window.location.origin);

        // Add query parameters
        Object.keys(params).forEach((key) => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.append(key, params[key]);
            }
        });

        const response = await fetch(url, {
            method: 'GET',
            headers: this.prepareHeaders()
        });

        return this.handleResponse(response);
    }

    // POST request
    async post(endpoint, data = {}) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'POST',
            headers: this.prepareHeaders(),
            body: JSON.stringify(data)
        });

        return this.handleResponse(response);
    }

    // PUT request
    async put(endpoint, data = {}) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'PUT',
            headers: this.prepareHeaders(),
            body: JSON.stringify(data)
        });

        return this.handleResponse(response);
    }

    // DELETE request
    async delete(endpoint) {
        const response = await fetch(this.baseURL + endpoint, {
            method: 'DELETE',
            headers: this.prepareHeaders()
        });

        return this.handleResponse(response);
    }

    // File upload
    async upload(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);

        // Add additional data
        Object.keys(additionalData).forEach((key) => {
            formData.append(key, additionalData[key]);
        });

        const response = await fetch(this.baseURL + endpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCsrfToken()
                // Don't set Content-Type for FormData
            },
            body: formData
        });

        return this.handleResponse(response);
    }
}

// Create singleton instance
export const api = new VivaCRMAPI();

export default api;
