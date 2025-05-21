/**
 * Import History JavaScript Module
 * VivaCRM v2
 */

// Import History Manager
class ImportHistoryManager {
    constructor() {
        this.init();
    }
    
    init() {
        // Filter form handling
        const filterForm = document.getElementById('importFilterForm');
        if (filterForm) {
            this.setupFilters(filterForm);
        }
        
        // Progress tracking for active imports
        this.trackActiveImports();
        
        // Setup tooltips
        this.setupTooltips();
        
        // Initialize charts if available
        this.initializeCharts();
    }
    
    setupFilters(form) {
        // Auto-submit on change
        const inputs = form.querySelectorAll('select, input[type="date"]');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                form.submit();
            });
        });
        
        // Clear filters button
        const clearBtn = document.getElementById('clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                form.reset();
                form.submit();
            });
        }
    }
    
    trackActiveImports() {
        const activeImports = document.querySelectorAll('[data-import-status="processing"]');
        if (activeImports.length > 0) {
            this.updateInterval = setInterval(() => {
                this.updateActiveImports();
            }, 5000); // Her 5 saniyede bir güncelle
        }
    }
    
    updateActiveImports() {
        const activeImports = document.querySelectorAll('[data-import-status="processing"]');
        activeImports.forEach(element => {
            const importId = element.dataset.importId;
            this.checkImportStatus(importId, element);
        });
    }
    
    async checkImportStatus(importId, element) {
        try {
            const response = await fetch(`/core/import/${importId}/status/`);
            const data = await response.json();
            
            if (data.status !== 'processing') {
                // Status changed, reload the page
                window.location.reload();
            } else {
                // Update progress if available
                if (data.progress) {
                    this.updateProgress(element, data.progress);
                }
            }
        } catch (error) {
            console.error('Status check failed:', error);
        }
    }
    
    updateProgress(element, progress) {
        const progressBar = element.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            progressBar.textContent = `${progress}%`;
        }
    }
    
    setupTooltips() {
        // Bootstrap tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(element => {
            new bootstrap.Tooltip(element);
        });
    }
    
    async reloadImport(importId) {
        if (!confirm('Bu import dosyasını yeniden yüklemek istediğinize emin misiniz?')) {
            return;
        }
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        try {
            const response = await fetch(`/core/import/${importId}/reload/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                alert(data.message || 'Yeniden yükleme başarısız oldu.');
            }
        } catch (error) {
            alert('Bir hata oluştu: ' + error.message);
        }
    }
    
    async previewFile(importId) {
        const modal = new bootstrap.Modal(document.getElementById('previewModal'));
        const contentEl = document.getElementById('previewContent');
        
        // Show loading
        contentEl.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Yükleniyor...</span>
                </div>
            </div>
        `;
        
        modal.show();
        
        try {
            const response = await fetch(`/core/import/${importId}/preview/`);
            const data = await response.json();
            
            if (data.error) {
                contentEl.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>${data.error}
                    </div>
                `;
                return;
            }
            
            this.renderPreviewTable(contentEl, data);
            
        } catch (error) {
            contentEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>Önizleme yüklenemedi: ${error.message}
                </div>
            `;
        }
    }
    
    renderPreviewTable(container, data) {
        let html = '<div class="table-responsive"><table class="table table-striped table-sm">';
        html += '<thead><tr>';
        
        // Headers
        data.columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Rows
        data.rows.forEach((row, index) => {
            html += '<tr>';
            row.forEach(cell => {
                const value = cell !== null ? cell : '';
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        
        if (data.total_rows > data.rows.length) {
            html += `<p class="text-muted text-center mt-2">İlk ${data.rows.length} satır gösteriliyor (Toplam: ${data.total_rows})</p>`;
        }
        
        container.innerHTML = html;
    }
    
    initializeCharts() {
        // Import statistics chart
        const statsChart = document.getElementById('importStatsChart');
        if (statsChart) {
            this.loadImportStats();
        }
    }
    
    async loadImportStats() {
        try {
            const response = await fetch('/core/import/stats/');
            const data = await response.json();
            
            this.renderStatsChart(data);
            this.renderModuleChart(data);
            this.updateRecentImports(data.recent);
            
        } catch (error) {
            console.error('Stats loading failed:', error);
        }
    }
    
    renderStatsChart(data) {
        const ctx = document.getElementById('dailyImportsChart');
        if (!ctx) return;
        
        const chartData = {
            labels: data.daily.map(d => d.date),
            datasets: [{
                label: 'Günlük Import Sayısı',
                data: data.daily.map(d => d.count),
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                tension: 0.1
            }]
        };
        
        new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    renderModuleChart(data) {
        const ctx = document.getElementById('moduleImportsChart');
        if (!ctx) return;
        
        const chartData = {
            labels: Object.keys(data.by_module),
            datasets: [{
                data: Object.values(data.by_module),
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(251, 146, 60, 0.8)',
                    'rgba(147, 51, 234, 0.8)'
                ]
            }]
        };
        
        new Chart(ctx, {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    updateRecentImports(recentImports) {
        const container = document.getElementById('recentImports');
        if (!container) return;
        
        let html = '';
        recentImports.forEach(imp => {
            const statusClass = imp.status === 'completed' ? 'success' : 
                               imp.status === 'failed' ? 'danger' : 'primary';
            
            html += `
                <div class="recent-import-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <a href="/core/import/${imp.id}/" class="fw-bold">${imp.filename}</a>
                            <div class="text-muted small">
                                <i class="bi bi-folder me-1"></i>${imp.module}
                                <span class="mx-1">•</span>
                                <i class="bi bi-person me-1"></i>${imp.created_by}
                            </div>
                        </div>
                        <div>
                            <span class="badge bg-${statusClass}">${this.getStatusText(imp.status)}</span>
                        </div>
                    </div>
                    <div class="text-muted small mt-1">
                        <i class="bi bi-clock me-1"></i>${imp.created_at}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    getStatusText(status) {
        const statusMap = {
            'processing': 'İşleniyor',
            'completed': 'Tamamlandı',
            'failed': 'Başarısız'
        };
        return statusMap[status] || status;
    }
    
    // Export functions for global use
    static filterByModule(module) {
        const form = document.getElementById('importFilterForm');
        const moduleSelect = form.querySelector('[name="module"]');
        moduleSelect.value = module;
        form.submit();
    }
    
    static filterByStatus(status) {
        const form = document.getElementById('importFilterForm');
        const statusSelect = form.querySelector('[name="status"]');
        statusSelect.value = status;
        form.submit();
    }
    
    static clearAllFilters() {
        const form = document.getElementById('importFilterForm');
        form.reset();
        form.submit();
    }
}

// Initialize on DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    window.importHistory = new ImportHistoryManager();
});

// Export for use in templates
window.ImportHistoryManager = ImportHistoryManager;