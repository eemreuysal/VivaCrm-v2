/**
 * HTMX Yardımcı Fonksiyonları
 *
 * VivaCRM projesi genelinde kullanılan HTMX olay işleyicileri ve yardımcı fonksiyonlar
 */

/**
 * HTMX olay işleyicilerini global olarak kaydeder
 */
document.addEventListener('DOMContentLoaded', () => {
    // Sayfa yüklendiğinde çalışan HTMX işlemleri
    registerGlobalEvents();
    setupToastMessages();
    setupFormValidation();
    initializeEventDelegation();
});

/**
 * Global HTMX olaylarını kaydeder
 */
function registerGlobalEvents() {
    // İstek başlamadan önce
    document.body.addEventListener('htmx:beforeRequest', (evt) => {
    // Çift gönderimi önle
        if (evt.detail.elt.tagName === 'FORM') {
            const submitButtons = evt.detail.elt.querySelectorAll('button[type="submit"]');
            submitButtons.forEach((button) => {
                button.disabled = true;
                button.classList.add('loading');
            });
        }
    });

    // İstek tamamlandıktan sonra
    document.body.addEventListener('htmx:afterRequest', (evt) => {
    // Form submit butonlarını tekrar aktif et
        if (evt.detail.elt.tagName === 'FORM') {
            const submitButtons = evt.detail.elt.querySelectorAll('button[type="submit"]');
            submitButtons.forEach((button) => {
                button.disabled = false;
                button.classList.remove('loading');
            });
        }
    });

    // İstek başarılı olduğunda
    document.body.addEventListener('htmx:afterOnLoad', (evt) => {
    // Modal içindeki formlar için, başarılı yanıtta modalı kapat
        if (evt.detail.xhr.status >= 200 && evt.detail.xhr.status < 300) {
            // Başarılı form gönderimi sonrası modal kapatma
            const form = evt.detail.elt;
            if (form.tagName === 'FORM' && isInsideModal(form)) {
                closeContainingModal(form);
            }
        }
    });

    // Doğrulama hatası olduğunda
    document.body.addEventListener('htmx:responseError', (evt) => {
    // Form doğrulama hatalarını işle
        if (evt.detail.xhr.status === 400) {
            try {
                const response = JSON.parse(evt.detail.xhr.responseText);
                if (response.errors) {
                    displayValidationErrors(evt.detail.elt, response.errors);
                }
            } catch (e) {
                console.error('Validation error response parsing failed', e);
            }
        }
    });
}

/**
 * Toast mesaj sistemini ayarlar
 */
function setupToastMessages() {
    // HTMX yanıtında toast mesajları için
    document.body.addEventListener('htmx:afterSwap', (_evt) => {
    // Toast mesajlarını kontrol et
        const messages = document.querySelectorAll('.htmx-message');

        messages.forEach((message) => {
            // Yeni toast mesajı oluştur
            createToast(
                message.dataset.message,
                message.dataset.type || 'info',
                message.dataset.duration || 5000
            );
            // Mesaj elementini kaldır
            message.remove();
        });
    });
}

/**
 * Toast mesajı oluşturur
 * @param {string} message - Mesaj içeriği
 * @param {string} type - Mesaj tipi (success, info, warning, error)
 * @param {number} duration - Gösterim süresi (ms)
 */
function createToast(message, type = 'info', duration = 5000) {
    // Toast konteynerini bul veya oluştur
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast toast-top toast-end z-50';
        document.body.appendChild(toastContainer);
    }

    // Yeni toast oluştur
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg animate-fadeIn`;
    toast.innerHTML = `
    <span>${message}</span>
    <button class="btn btn-sm btn-ghost">✕</button>
  `;

    // Kapat butonu
    const closeBtn = toast.querySelector('button');
    closeBtn.addEventListener('click', () => {
        toast.classList.add('animate-fadeOut');
        setTimeout(() => {
            toast.remove();
        }, 300);
    });

    // Toastı konteyner'a ekle
    toastContainer.appendChild(toast);

    // Otomatik kapanma
    if (duration > 0) {
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.add('animate-fadeOut');
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }
        }, duration);
    }

    return toast;
}

/**
 * Form doğrulama işlevselliğini ayarlar
 */
function setupFormValidation() {
    // Client-side doğrulama
    document.body.addEventListener('htmx:validation:validate', (evt) => {
        const form = evt.detail.elt;
        const isValid = validateForm(form);
        evt.detail.valid = isValid;

        if (!isValid) {
            evt.preventDefault();
        }
    });
}

/**
 * Formu client tarafında doğrular
 * @param {HTMLFormElement} form - Doğrulanacak form
 * @returns {boolean} - Form geçerli mi?
 */
function validateForm(form) {
    // HTML5 doğrulama
    if (!form.checkValidity()) {
    // Genel hata mesajını göster
        form.reportValidity();
        return false;
    }

    return true;
}

/**
 * Sunucu tarafından dönen doğrulama hatalarını form üzerinde gösterir
 * @param {HTMLElement} form - Hata gösterilecek form
 * @param {Object} errors - Sunucudan dönen hata nesnesi
 */
function displayValidationErrors(form, errors) {
    // Önceki hata mesajlarını temizle
    form.querySelectorAll('.error-message').forEach((el) => el.remove());
    form.querySelectorAll('.is-invalid').forEach((el) => el.classList.remove('is-invalid'));

    // Her bir hata için
    Object.entries(errors).forEach(([fieldName, errorMessages]) => {
    // Alan adına göre ilgili input'u bul
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            // Hata stilini uygula
            field.classList.add('is-invalid');

            // Hata mesajı oluştur
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message text-error text-sm mt-1';
            errorDiv.innerText = Array.isArray(errorMessages)
                ? errorMessages.join(', ')
                : errorMessages;

            // Mesajı input'un altına ekle
            field.parentNode.appendChild(errorDiv);
        } else if (fieldName === '__all__' || fieldName === 'non_field_errors') {
            // Genel form hatası
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message text-error text-sm mt-4 mb-2 p-3 bg-error/10 rounded-lg';
            errorDiv.innerText = Array.isArray(errorMessages)
                ? errorMessages.join(', ')
                : errorMessages;

            // Form başlangıcına ekle
            form.prepend(errorDiv);
        }
    });
}

/**
 * Bir elementin modal içinde olup olmadığını kontrol eder
 * @param {HTMLElement} element - Kontrol edilecek element
 * @returns {boolean} - Element bir modal içinde mi?
 */
function isInsideModal(element) {
    let parent = element.parentElement;
    while (parent !== null) {
        if (parent.classList.contains('modal-box')) {
            return true;
        }
        parent = parent.parentElement;
    }
    return false;
}

/**
 * Bir elementi içeren modalı kapatır
 * @param {HTMLElement} element - İçerik elementi
 */
function closeContainingModal(element) {
    let parent = element.parentElement;
    let modalId = null;

    // Modal bileşenini bul
    while (parent !== null) {
        if (parent.hasAttribute('x-data') && parent.getAttribute('x-data').includes('modal')) {
            modalId = parent.id;
            break;
        }
        parent = parent.parentElement;
    }

    if (modalId) {
    // Modal kapatma eventini gönder
        document.getElementById(modalId).dispatchEvent(
            new CustomEvent('close-modal', { bubbles: true })
        );
    }
}

/**
 * Olay delegasyonunu başlatır (performans için)
 */
function initializeEventDelegation() {
    // Tıklama olaylarını delege et
    document.body.addEventListener('click', (evt) => {
    // Tablo sıralaması
        if (evt.target.closest('.sortable')) {
            handleTableSort(evt);
        }

        // Filtreleme
        if (evt.target.closest('[data-filter]')) {
            handleFilter(evt);
        }
    });
}

/**
 * Tablo sıralama işlemi
 * @param {Event} evt - Olay nesnesi
 */
function handleTableSort(evt) {
    const sortableHeader = evt.target.closest('.sortable');
    if (!sortableHeader) return;

    const sortField = sortableHeader.dataset.sortField;
    const currentSortDir = sortableHeader.dataset.sortDir || 'asc';
    const newSortDir = currentSortDir === 'asc' ? 'desc' : 'asc';

    // URL güncelleme
    const url = new URL(window.location);
    url.searchParams.set('sort_by', sortField);
    url.searchParams.set('sort_dir', newSortDir);

    // Mevcut sayfayı koru
    const currentPage = url.searchParams.get('page');
    if (currentPage) {
        url.searchParams.set('page', currentPage);
    }

    // HTMX isteği
    htmx.ajax('GET', url.toString(), { target: '#products-table', swap: 'outerHTML' });
}

/**
 * Filtre işlemi
 * @param {Event} evt - Olay nesnesi
 */
function handleFilter(evt) {
    const filterElement = evt.target.closest('[data-filter]');
    if (!filterElement) return;

    const filterName = filterElement.dataset.filter;
    const filterValue = filterElement.dataset.value;

    // URL güncelleme
    const url = new URL(window.location);

    if (filterValue === 'clear') {
        url.searchParams.delete(filterName);
    } else {
        url.searchParams.set(filterName, filterValue);
    }

    // Sıralama parametrelerini koru
    const sortBy = url.searchParams.get('sort_by');
    const sortDir = url.searchParams.get('sort_dir');

    if (sortBy) url.searchParams.set('sort_by', sortBy);
    if (sortDir) url.searchParams.set('sort_dir', sortDir);

    // Sayfa numarasını sıfırla
    url.searchParams.delete('page');

    // HTMX isteği
    htmx.ajax('GET', url.toString(), { target: '#products-table', swap: 'outerHTML' });
}
