# core/admin_import.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models_import import ImportTask, ImportSummary, DetailedImportResult


@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    """İçe aktarma görevleri yönetimi"""
    list_display = ['file_name', 'type', 'status', 'progress_bar', 'created_by', 'created_at', 'view_summary']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['file_name', 'created_by__username']
    readonly_fields = ['created_at', 'started_at', 'completed_at', 'progress', 'current_row']
    
    def progress_bar(self, obj):
        """İlerleme çubuğu göster"""
        if obj.progress == 0:
            color = 'gray'
        elif obj.progress < 100:
            color = 'blue'
        else:
            color = 'green'
            
        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:5px;">'
            '<div style="width:{}%; background-color:{}; height:20px; border-radius:5px; text-align:center; color:white;">{}</div>'
            '</div>',
            obj.progress,
            color,
            f'{obj.progress}%'
        )
    progress_bar.short_description = 'İlerleme'
    
    def view_summary(self, obj):
        """Özet görüntüleme linki"""
        url = reverse('import:task_summary', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Özeti Görüntüle</a>', url)
    view_summary.short_description = 'Özet'


@admin.register(ImportSummary)
class ImportSummaryAdmin(admin.ModelAdmin):
    """İçe aktarma özetleri yönetimi"""
    list_display = ['import_task', 'total_rows', 'successful_rows', 'failed_rows', 
                   'partial_rows', 'success_rate_display', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['import_task', 'total_rows', 'successful_rows', 'failed_rows',
                      'skipped_rows', 'partial_rows', 'created_count', 'updated_count',
                      'field_success_rates', 'error_summary', 'processing_time',
                      'created_at', 'updated_at']
    
    def success_rate_display(self, obj):
        """Başarı oranını göster"""
        return f'{obj.success_rate:.1f}%'
    success_rate_display.short_description = 'Başarı Oranı'


@admin.register(DetailedImportResult)
class DetailedImportResultAdmin(admin.ModelAdmin):
    """Detaylı içe aktarma sonuçları yönetimi"""
    list_display = ['import_task', 'row_number', 'status', 'error_preview', 'created_at']
    list_filter = ['status', 'created_at', 'import_task']
    search_fields = ['error_message', 'data']
    readonly_fields = ['import_task', 'row_number', 'status', 'data',
                      'fields_updated', 'fields_failed', 'error_message',
                      'error_details', 'dependent_operations', 'created_at']
    
    def error_preview(self, obj):
        """Hata önizlemesi"""
        if obj.error_message:
            return obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
        return '-'
    error_preview.short_description = 'Hata'
    
    def has_add_permission(self, request):
        """Yeni kayıt eklemeyi engelle"""
        return False