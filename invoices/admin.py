from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ['description', 'quantity', 'unit_price', 'tax_rate', 'discount_amount', 'line_total', 'tax_amount', 'total_with_tax']
    readonly_fields = ['line_total', 'tax_amount', 'total_with_tax']


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'order', 'invoice_type', 'status', 'issue_date', 'due_date', 'total_amount', 'is_sent']
    list_filter = ['status', 'invoice_type', 'issue_date', 'is_sent']
    search_fields = ['invoice_number', 'order__order_number', 'order__customer__name']
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline]
    readonly_fields = ['created_at', 'updated_at', 'total_amount', 'subtotal', 'tax_amount']
    
    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'order', 'invoice_type', 'status')
        }),
        (_('Tarihler'), {
            'fields': ('issue_date', 'due_date', 'created_at', 'updated_at')
        }),
        (_('Tutarlar'), {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total_amount')
        }),
        (_('PDF/Email'), {
            'fields': ('pdf_file', 'is_sent', 'sent_date')
        }),
        (_('Ek Bilgiler'), {
            'fields': ('notes', 'created_by')
        }),
    )


admin.site.register(Invoice, InvoiceAdmin)