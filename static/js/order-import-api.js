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
        
        const formData = new FormData();
        const file = excelFile.files[0];
        
        if (!file) {
            showAlert('error', 'Lütfen bir dosya seçin.');
            return;
        }
        
        formData.append('file', file);
        
        // Show loading state
        dropArea.classList.add('loading-active');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading loading-spinner loading-sm mr-2"></span>İçe Aktarılıyor...';
        
        // Update step
        updateSteps(4);
        
        // Submit form via AJAX
        console.log('Submitting to:', '/orders/import-api/');
        fetch('/orders/import-api/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
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
        const errorDiv = document.createElement('div');
        errorDiv.className = 'card bg-error/10 border border-error p-4 mb-6 animate-fade-in';
        errorDiv.innerHTML = `
            <h3 class="font-bold text-error mb-3">İçe Aktarma Hataları</h3>
            <div class="space-y-2">
                ${data.errors.map(error => `
                    <div class="text-sm">
                        <span class="font-medium">Satır ${error.row}:</span> ${error.message}
                    </div>
                `).join('')}
            </div>
            ${data.error_summary ? `
                <div class="mt-4 pt-4 border-t border-error/20">
                    <p class="text-sm font-medium">Özet: ${data.error_summary.total_errors} hata, ${data.error_summary.total_warnings || 0} uyarı</p>
                </div>
            ` : ''}
        `;
        
        const container = document.querySelector('.container');
        const form = container.querySelector('.card');
        container.insertBefore(errorDiv, form);
    }
    
    // Get cookie value by name
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});