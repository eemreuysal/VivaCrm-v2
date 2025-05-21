from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem, Payment, Shipment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'tax_rate', 'discount_amount', 'line_total', 'tax_amount', 'total_with_tax']
    readonly_fields = ['line_total', 'tax_amount', 'total_with_tax']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['payment_method', 'amount', 'payment_date', 'transaction_id', 'is_successful']


class ShipmentInline(admin.TabularInline):
    model = Shipment
    extra = 0
    fields = ['carrier', 'tracking_number', 'shipping_date', 'status', 'estimated_delivery', 'actual_delivery']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'payment_status', 'segment', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'segment', 'payment_method', 'created_at']
    search_fields = ['order_number', 'customer__name', 'customer__company_name', 'notes']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline, PaymentInline, ShipmentInline]
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount']
    fieldsets = (
        (None, {
            'fields': ('order_number', 'customer', 'status', 'order_date', 'notes')
        }),
        (_('Adres Bilgileri'), {
            'fields': ('billing_address', 'shipping_address')
        }),
        (_('Ödeme Bilgileri'), {
            'fields': ('payment_method', 'payment_status', 'payment_notes')
        }),
        (_('Tutarlar'), {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total_amount')
        }),
        (_('Diğer Bilgiler'), {
            'fields': ('owner', 'shipping_date', 'delivery_date')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'amount', 'payment_date', 'is_successful']
    list_filter = ['payment_method', 'is_successful', 'payment_date']
    search_fields = ['order__order_number', 'transaction_id', 'notes']
    date_hierarchy = 'payment_date'


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['order', 'carrier', 'tracking_number', 'status', 'shipping_date', 'actual_delivery']
    list_filter = ['status', 'carrier', 'shipping_date']
    search_fields = ['order__order_number', 'tracking_number', 'notes']
    date_hierarchy = 'shipping_date'