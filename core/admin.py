from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ValidationRule, RuleSet, ValidationLog
import json


@admin.register(ValidationRule)
class ValidationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'created_at', 'updated_at')
    list_filter = ('rule_type', 'created_at')
    search_fields = ('name', 'error_message')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'rule_type', 'error_message')
        }),
        (_('Parametreler'), {
            'fields': ('parameters',),
            'classes': ('wide',),
        }),
        (_('Tarihler'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'parameters':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget
            kwargs['widget'].attrs['style'] = 'font-family: monospace; width: 100%;'
        return super().formfield_for_dbfield(db_field, **kwargs)


@admin.register(RuleSet)
class RuleSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name', 'field_name', 'is_active', 'rule_count', 'created_at')
    list_filter = ('is_active', 'model_name', 'created_at')
    search_fields = ('name', 'description', 'model_name', 'field_name')
    filter_horizontal = ('rules',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'model_name', 'field_name', 'is_active')
        }),
        (_('Kurallar'), {
            'fields': ('rules',),
            'classes': ('wide',),
        }),
        (_('Bilgiler'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    def rule_count(self, obj):
        return obj.rules.count()
    rule_count.short_description = _('Kural Sayısı')
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ValidationLog)
class ValidationLogAdmin(admin.ModelAdmin):
    list_display = ('rule_set', 'value_short', 'is_valid', 'error_count', 'created_at')
    list_filter = ('is_valid', 'created_at', 'rule_set')
    search_fields = ('value', 'errors')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('rule_set', 'value', 'is_valid')
        }),
        (_('Hatalar'), {
            'fields': ('errors',),
            'classes': ('wide',),
        }),
        (_('Tarih'), {
            'fields': ('created_at',),
        }),
    )
    
    readonly_fields = ('created_at', 'errors', 'is_valid', 'value')
    
    def value_short(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_short.short_description = _('Değer')
    
    def error_count(self, obj):
        return len(obj.errors) if obj.errors else 0
    error_count.short_description = _('Hata Sayısı')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of logs
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing of logs