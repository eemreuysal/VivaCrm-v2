from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import SavedReport


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'owner', 'is_shared', 'created_at']
    list_filter = ['type', 'is_shared', 'created_at', 'owner']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'type', 'description', 'parameters')
        }),
        (_('Paylaşım Bilgileri'), {
            'fields': ('owner', 'is_shared')
        }),
        (_('Tarih Bilgileri'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )