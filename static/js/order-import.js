document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('dropArea');
    const excelFile = document.getElementById('excelFile');
    const filePreview = document.getElementById('filePreview');
    const selectedFileName = document.getElementById('selectedFileName');
    const selectedFileSize = document.getElementById('selectedFileSize');
    const removeFile = document.getElementById('removeFile');
    const submitBtn = document.getElementById('submitBtn');
    const importForm = document.getElementById('importForm');
    
    // Prevent default behavior for dragover and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('dragging');
    }
    
    function unhighlight() {
        dropArea.classList.remove('dragging');
    }
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            excelFile.files = files;
            updateFilePreview();
        }
    }
    
    // Handle file selection via input
    excelFile.addEventListener('change', updateFilePreview);
    
    // Update file preview when a file is selected
    function updateFilePreview() {
        if (excelFile.files && excelFile.files[0]) {
            const file = excelFile.files[0];
            
            // Check if file is an Excel file
            if (!file.name.match(/\.(xlsx|xls)$/i)) {
                showAlert('error', 'Lütfen geçerli bir Excel dosyası (.xlsx veya .xls) seçin.');
                resetFileInput();
                return;
            }
            
            // Format file size
            let size = file.size;
            let sizeStr = '';
            
            if (size < 1024) {
                sizeStr = size + ' bytes';
            } else if (size < 1024 * 1024) {
                sizeStr = (size / 1024).toFixed(2) + ' KB';
            } else {
                sizeStr = (size / (1024 * 1024)).toFixed(2) + ' MB';
            }
            
            selectedFileName.textContent = file.name;
            selectedFileSize.textContent = sizeStr;
            filePreview.classList.add('active');
            submitBtn.disabled = false;
            
            // Update steps
            updateSteps(3);
        }
    }
    
    // Remove selected file
    removeFile.addEventListener('click', resetFileInput);
    
    function resetFileInput() {
        excelFile.value = '';
        filePreview.classList.remove('active');
        submitBtn.disabled = true;
        
        // Reset steps
        updateSteps(1);
    }
    
    // Update process steps
    function updateSteps(activeStep) {
        const steps = document.querySelectorAll('.step');
        
        steps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            
            if (index + 1 < activeStep) {
                step.classList.add('completed');
            }
            
            if (index + 1 === activeStep) {
                step.classList.add('active');
            }
        });
    }
    
    // Toggle accordion items
    window.toggleAccordion = function(header) {
        const accordionItem = header.parentElement;
        accordionItem.classList.toggle('open');
    }
    
    // Show alerts
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} mb-4 animate-fade-in`;
        
        let icon = '';
        if (type === 'error') {
            icon = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />';
        } else if (type === 'warning') {
            icon = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />';
        } else {
            icon = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />';
        }
        
        alertDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                ${icon}
            </svg>
            <span>${message}</span>
        `;
        
        const container = document.querySelector('.container');
        const firstChild = container.firstChild;
        container.insertBefore(alertDiv, firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    // Handle form submission with AJAX
    importForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(importForm);
        const file = formData.get('excel_file');
        
        if (!file || file.size === 0) {
            showAlert('error', 'Lütfen bir dosya seçin.');
            return;
        }
        
        // Show loading state
        dropArea.classList.add('loading-active');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading loading-spinner loading-sm mr-2"></span>İçe Aktarılıyor...';
        
        // Create new FormData with correct field name for API
        const apiFormData = new FormData();
        apiFormData.append('file', file);  // API expects 'file' not 'excel_file'
        apiFormData.append('csrfmiddlewaretoken', formData.get('csrfmiddlewaretoken'));
        
        // Debug: FormData içeriğini logla
        console.log('FormData entries:');
        for (let [key, value] of apiFormData.entries()) {
            console.log(`${key}:`, value);
        }
        
        // Update step
        updateSteps(4);
        
        // Submit form via AJAX - API'ye gönder
        const apiUrl = '/api/v1/orders/order-import/';
        console.log('Submitting to:', apiUrl);
        fetch(apiUrl, {
            method: 'POST',
            body: apiFormData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            credentials: 'include'
        })
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            console.log('Content-Type:', response.headers.get('content-type'));
            
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Error response text:', text);
                    console.error('Error status:', response.status);
                    console.error('Error statusText:', response.statusText);
                    throw new Error(`HTTP error! status: ${response.status}`);
                });
            }
            
            // Content-Type kontrolü
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Expected JSON response but got:', contentType);
                return response.text().then(text => {
                    console.error('Non-JSON response:', text);
                    throw new Error('Response is not JSON');
                });
            }
            
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            
            // Detaylı hata logu
            if (data.errors && data.errors.length > 0) {
                console.log('Error details:');
                data.errors.forEach((error, index) => {
                    console.log(`Error ${index + 1}:`, {
                        row: error.row,
                        column: error.column,
                        message: error.message,
                        error_key: error.error_key,
                        value: error.value
                    });
                });
            }
            
            if (data.success) {
                showAlert('success', `İçe aktarma başarıyla tamamlandı. ${data.created_count} sipariş oluşturuldu.`);
                // Redirect after short delay
                setTimeout(() => {
                    window.location.href = '/orders/';
                }, 2000);
            } else if (data.error_count > 0 && data.errors) {
                // Show error summary
                displayImportErrors(data);
                if (data.created_count > 0) {
                    showAlert('warning', `${data.created_count} sipariş oluşturuldu, ${data.error_count} hata oluştu.`);
                } else {
                    showAlert('error', `Hiç sipariş oluşturulamadı. ${data.error_count} hata oluştu.`);
                }
            } else if (data.error) {
                showAlert('error', data.error);
            } else {
                showAlert('error', 'İçe aktarma sırasında bir hata oluştu.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('error', 'İçe aktarma sırasında bir hata oluştu. Lütfen tekrar deneyin.');
        })
        .finally(() => {
            // Reset loading state
            dropArea.classList.remove('loading-active');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4 4m0 0l-4-4m4 4V4" /></svg>İçe Aktar';
        });
    });
    
    // Display import errors
    function displayImportErrors(data) {
        // Mevcut hata div'ini kaldır
        const existingError = document.querySelector('.import-errors');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'card bg-error/10 border border-error p-4 mb-6 animate-fade-in import-errors';
        
        // Error formatını kontrol et
        const errors = data.errors || [];
        const errorMessages = errors.map(error => {
            // API response'tan gelen hata formatına göre düzenle
            let message = error.message || 'Bilinmeyen hata';
            let row = error.row || error.error_key || 'Bilinmeyen';
            let column = error.column || '';
            
            return `
                <div class="text-sm">
                    <span class="font-medium">Satır ${row}${column ? ', Sütun ' + column : ''}:</span> ${message}
                </div>
            `;
        }).join('');
        
        errorDiv.innerHTML = `
            <h3 class="font-bold text-error mb-3">İçe Aktarma Hataları</h3>
            <div class="space-y-2">
                ${errorMessages}
            </div>
            ${data.error_summary ? `
                <div class="mt-4 pt-4 border-t border-error/20">
                    <p class="text-sm font-medium">Özet: ${data.error_summary.total_errors} hata, ${data.error_summary.total_warnings || 0} uyarı</p>
                </div>
            ` : ''}
        `;
        
        // Container'ı bul ve hata div'ini ekle
        const container = document.querySelector('.container');
        if (container) {
            // İlk child'ın önüne ekle
            if (container.firstChild) {
                container.insertBefore(errorDiv, container.firstChild);
            } else {
                container.appendChild(errorDiv);
            }
            
            // Sayfanın üstüne scroll et
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    // Real-time file preview (optional advanced feature)
    function previewExcelFile(file) {
        // This would require a library like SheetJS to parse Excel files in the browser
        // For now, we'll just show a simple preview modal
        const modal = document.getElementById('filePreviewModal');
        const content = document.getElementById('filePreviewContent');
        
        content.innerHTML = `
            <div class="text-center p-8">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-success mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p class="text-lg font-medium">${file.name}</p>
                <p class="text-sm text-base-content/70 mt-2">Dosya önizleme için sunucuya yüklenecek</p>
            </div>
        `;
        
        modal.classList.add('modal-open');
    }
    
    // Close preview modal
    window.closePreviewModal = function() {
        const modal = document.getElementById('filePreviewModal');
        modal.classList.remove('modal-open');
    }
    
    // Confirm import from preview
    window.confirmImport = function() {
        closePreviewModal();
        importForm.submit();
    }
    
    // WebSocket support for real-time progress (optional)
    function connectWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/import/`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'progress') {
                updateProgressBar(data.progress);
            } else if (data.type === 'complete') {
                showAlert('success', data.message);
            } else if (data.type === 'error') {
                showAlert('error', data.message);
            }
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        return ws;
    }
    
    // Update progress bar
    function updateProgressBar(progress) {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress progress-primary mt-4';
        progressBar.innerHTML = `<div class="progress-bar" style="width: ${progress}%"></div>`;
        
        const existingBar = document.querySelector('.progress');
        if (existingBar) {
            existingBar.querySelector('.progress-bar').style.width = progress + '%';
        } else {
            filePreview.appendChild(progressBar);
        }
    }
    
    // If there are error messages, highlight the troubleshooting section
    const errorMessages = document.querySelectorAll('.alert-error');
    if (errorMessages.length > 0) {
        const firstCollapse = document.querySelector('.collapse input');
        if (firstCollapse) {
            firstCollapse.checked = true;
        }
    }
});