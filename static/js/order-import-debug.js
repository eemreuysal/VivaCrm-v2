// Debug version of order-import.js
console.log('order-import-debug.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded - initializing order import');
    
    const dropArea = document.getElementById('dropArea');
    const excelFile = document.getElementById('excelFile');
    const filePreview = document.getElementById('filePreview');
    const selectedFileName = document.getElementById('selectedFileName');
    const selectedFileSize = document.getElementById('selectedFileSize');
    const removeFile = document.getElementById('removeFile');
    const submitBtn = document.getElementById('submitBtn');
    const importForm = document.getElementById('importForm');
    
    console.log('Elements found:', {
        dropArea: !!dropArea,
        excelFile: !!excelFile,
        filePreview: !!filePreview,
        submitBtn: !!submitBtn,
        importForm: !!importForm
    });
    
    if (!importForm) {
        console.error('importForm not found!');
        return;
    }
    
    // Handle form submission
    importForm.addEventListener('submit', function(e) {
        console.log('Form submit event triggered');
        e.preventDefault();
        
        const formData = new FormData(importForm);
        
        // Log FormData contents
        console.log('FormData contents:');
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}:`, value);
        }
        
        console.log('Form action:', importForm.action);
        console.log('Making AJAX request...');
        
        fetch(importForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => {
            console.log('Response received:', {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers,
                contentType: response.headers.get('content-type')
            });
            
            if (!response.ok) {
                console.error('Response not OK, getting text...');
                return response.text().then(text => {
                    console.error('Error response text:', text);
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                });
            }
            
            return response.json();
        })
        .then(data => {
            console.log('Success response:', data);
            if (data.success) {
                alert('Başarılı: ' + data.message);
            } else {
                alert('Hata: ' + (data.message || 'Bilinmeyen hata'));
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('Hata: ' + error.message);
        });
    });
});