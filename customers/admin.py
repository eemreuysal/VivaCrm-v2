from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Customer, Address, Contact


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'email', 'phone', 'is_active', 'total_orders', 'owner']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['name', 'company_name', 'email', 'phone', 'tax_number']
    date_hierarchy = 'created_at'
    inlines = [AddressInline, ContactInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'type', 'email', 'phone', 'website'),
        }),
        (_('Şirket Bilgileri'), {
            'fields': ('company_name', 'tax_office', 'tax_number'),
            'classes': ('collapse',),
        }),
        (_('Ek Bilgiler'), {
            'fields': ('notes', 'owner', 'is_active'),
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'type', 'city', 'is_default']
    list_filter = ['type', 'is_default', 'city', 'country']
    search_fields = ['title', 'address_line1', 'address_line2', 'city', 'postal_code', 'customer__name']
    list_select_related = ['customer']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer', 'title', 'email', 'phone', 'is_primary']
    list_filter = ['is_primary', 'department']
    search_fields = ['name', 'email', 'phone', 'customer__name']
    list_select_related = ['customer']