// VivaCRM - Forms Component
import { store } from '../store/index.js';
import { createAlpineComponent } from '../core/base-component.js';
import { utils } from '../core/utils.js';

export const formComponent = () => createAlpineComponent({
    loading: false,
    errors: {},
    dirty: false,
    savedData: {},

    init() {
        // Save initial form data
        this.savedData = this.getFormData();

        // Track form changes
        this.$watch('$el', () => {
            this.dirty = JSON.stringify(this.getFormData()) !== JSON.stringify(this.savedData);
        });

        // Warn before leaving with unsaved changes - otomatik temizlenecek
        this.addEventListener(window, 'beforeunload', (e) => {
            if (this.dirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    },

    getFormData() {
        const formData = {};
        const form = this.$el.closest('form');
        if (form) {
            const data = new FormData(form);
            for (const [key, value] of data.entries()) {
                formData[key] = value;
            }
        }
        return formData;
    },

    async submitForm(e) {
        e.preventDefault();
        this.loading = true;
        this.errors = {};

        const form = e.target;
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.VivaCRM?.csrfToken || ''
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.handleSuccess(data);
            } else {
                this.handleError(data);
            }
        } catch (error) {
            console.error('Form submission error:', error);
            store.addNotification({
                type: 'error',
                message: 'Form gönderilirken bir hata oluştu',
                timeout: 5000
            });
        } finally {
            this.loading = false;
        }
    },

    handleSuccess(data) {
        this.dirty = false;
        store.addNotification({
            type: 'success',
            message: data.message || 'İşlem başarıyla tamamlandı',
            timeout: 5000
        });

        // Redirect if URL provided
        if (data.redirect_url) {
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1000);
        }
    },

    handleError(data) {
        if (data.errors) {
            this.errors = data.errors;

            // Scroll to first error field
            const firstError = Object.keys(this.errors)[0];
            const errorField = document.querySelector(`[name="${firstError}"]`);
            if (errorField) {
                errorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                errorField.focus();
            }
        }

        store.addNotification({
            type: 'error',
            message: data.message || 'Lütfen hataları düzeltin',
            timeout: 7000
        });
    },

    clearError(field) {
        delete this.errors[field];
    },

    hasError(field) {
        return Object.prototype.hasOwnProperty.call(this.errors, field);
    },

    getError(field) {
        return this.errors[field] || '';
    },

    reset() {
        this.errors = {};
        this.dirty = false;
        this.loading = false;
        this.$el.closest('form')?.reset();
    }
});

// Excel upload component
export const excelUploadComponent = () => createAlpineComponent({
    uploading: false,
    progress: 0,
    file: null,
    dragActive: false,
    errors: [],
    preview: null,

    init() {
        // Setup drag and drop
        this.setupDragDrop();
    },

    setupDragDrop() {
        const dropZone = this.$el.querySelector('.drop-zone');
        if (!dropZone) return;

        // Prevent defaults with automatic cleanup
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
            this.addEventListener(dropZone, eventName, this.preventDefaults, false);
        });

        // Drag active state handlers
        ['dragenter', 'dragover'].forEach((eventName) => {
            this.addEventListener(dropZone, eventName, () => (this.dragActive = true), false);
        });

        ['dragleave', 'drop'].forEach((eventName) => {
            this.addEventListener(dropZone, eventName, () => (this.dragActive = false), false);
        });

        // Drop handler
        this.addEventListener(dropZone, 'drop', this.handleDrop.bind(this), false);
    },

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    handleDrop(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    },

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    },

    handleFile(file) {
        // Validate file type
        const validTypes = [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];

        if (!validTypes.includes(file.type)) {
            store.addNotification({
                type: 'error',
                message: 'Lütfen geçerli bir Excel dosyası seçin (.xls veya .xlsx)',
                timeout: 5000
            });
            return;
        }

        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            store.addNotification({
                type: 'error',
                message: 'Dosya boyutu çok büyük (max 10MB)',
                timeout: 5000
            });
            return;
        }

        this.file = file;
        this.previewFile();
    },

    async previewFile() {
        if (!this.file) return;

        const formData = new FormData();
        formData.append('file', this.file);
        formData.append('preview', 'true');

        try {
            const response = await fetch('/excel/preview/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.VivaCRM?.csrfToken || ''
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.preview = data;
            } else {
                throw new Error('Preview failed');
            }
        } catch (error) {
            console.error('Preview error:', error);
            store.addNotification({
                type: 'error',
                message: 'Önizleme yüklenemedi',
                timeout: 5000
            });
        }
    },

    async startUpload() {
        if (!this.file) return;

        this.uploading = true;
        this.progress = 0;
        this.errors = [];

        const formData = new FormData();
        formData.append('file', this.file);

        try {
            const controller = this.createAbortController();
            this.currentUploadController = controller;

            // API call with fetch for better control
            const csrfToken = utils.getCookie('csrftoken') || window.VivaCRM?.csrfToken || '';

            const response = await fetch('/excel/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData,
                signal: controller.signal
            });

            const data = await response.json();

            if (response.ok) {
                this.completeUpload(data);
            } else {
                this.handleUploadError(data);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Upload cancelled');
                return;
            }
            console.error('Upload error:', error);
            this.handleUploadError({ message: 'Beklenmeyen bir hata oluştu' });
        }
    },

    completeUpload(response) {
        this.uploading = false;
        this.progress = 100;

        if (response.errors && response.errors.length > 0) {
            this.errors = response.errors;
            store.addNotification({
                type: 'warning',
                message: `Yükleme tamamlandı ancak ${response.errors.length} hata bulundu`,
                timeout: 7000
            });
        } else {
            store.addNotification({
                type: 'success',
                message: response.message || 'Excel yükleme başarıyla tamamlandı',
                timeout: 5000
            });

            // Reset form - otomatik temizlenecek
            this.setTimeout(() => {
                this.reset();
            }, 2000);
        }
    },

    handleUploadError(error) {
        this.uploading = false;
        this.progress = 0;

        store.addNotification({
            type: 'error',
            message: error.message || 'Yükleme sırasında bir hata oluştu',
            timeout: 7000
        });
    },

    cancelUpload() {
        // Abort ongoing upload
        if (this.currentUploadController) {
            this.currentUploadController.abort();
            this.currentUploadController = null;
        }
        this.reset();
    },

    reset() {
        this.file = null;
        this.uploading = false;
        this.progress = 0;
        this.errors = [];
        this.preview = null;
        this.dragActive = false;

        // Clear file input
        const fileInput = this.$el.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.value = '';
        }
    }

});

// File upload component
export const fileUploadComponent = () => createAlpineComponent({
    files: [],
    uploading: false,
    maxFiles: 5,
    maxFileSize: 5 * 1024 * 1024, // 5MB
    acceptedTypes: ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'],

    init() {
        this.setupDragDrop();
    },

    setupDragDrop() {
        // Similar to excel upload setup
        // Reuse the same pattern
    },

    handleFiles(fileList) {
        const files = Array.from(fileList);

        for (const file of files) {
            if (this.validateFile(file)) {
                this.files.push({
                    file: file,
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    preview: null,
                    progress: 0,
                    error: null
                });

                // Generate preview for images
                if (file.type.startsWith('image/')) {
                    this.generatePreview(file);
                }
            }
        }
    },

    validateFile(file) {
        if (!this.acceptedTypes.includes(file.type)) {
            store.addNotification({
                type: 'error',
                message: `Dosya türü desteklenmiyor: ${file.type}`,
                timeout: 5000
            });
            return false;
        }

        if (file.size > this.maxFileSize) {
            store.addNotification({
                type: 'error',
                message: `Dosya çok büyük: ${utils.formatFileSize(file.size)} ` +
                        `(max: ${utils.formatFileSize(this.maxFileSize)})`,
                timeout: 5000
            });
            return false;
        }

        if (this.files.length >= this.maxFiles) {
            store.addNotification({
                type: 'error',
                message: `Maksimum dosya sayısına ulaşıldı (${this.maxFiles})`,
                timeout: 5000
            });
            return false;
        }

        return true;
    },

    generatePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const fileItem = this.files.find((f) => f.file === file);
            if (fileItem) {
                fileItem.preview = e.target.result;
            }
        };
        reader.readAsDataURL(file);
    },

    removeFile(index) {
        this.files.splice(index, 1);
    },

    async uploadFiles() {
        if (this.files.length === 0) return;

        this.uploading = true;

        for (const fileItem of this.files) {
            await this.uploadFile(fileItem);
        }

        this.uploading = false;

        // Remove successfully uploaded files
        this.files = this.files.filter((f) => f.error !== null);

        if (this.files.length === 0) {
            store.addNotification({
                type: 'success',
                message: 'Tüm dosyalar başarıyla yüklendi',
                timeout: 5000
            });
        }
    },

    async uploadFile(fileItem) {
        const formData = new FormData();
        formData.append('file', fileItem.file);

        try {
            const response = await fetch('/files/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': window.VivaCRM?.csrfToken || ''
                }
            });

            if (response.ok) {
                fileItem.progress = 100;
            } else {
                fileItem.error = 'Yükleme başarısız oldu';
            }
        } catch (error) {
            fileItem.error = 'Bağlantı hatası';
        }
    }

});

// Register components with Alpine
if (window.Alpine) {
    Alpine.data('formComponent', formComponent);
    Alpine.data('excelUploadComponent', excelUploadComponent);
    Alpine.data('fileUploadComponent', fileUploadComponent);
}

// Export for module usage
export default {
    init: () => {
        // Forms component loaded successfully
    }
};
