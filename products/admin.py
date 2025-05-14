from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Category, Product, ProductImage, ProductAttribute, 
    ProductAttributeValue, StockMovement
)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'price', 'tax_rate', 'stock', 'status', 'is_active']
    list_filter = ['category', 'status', 'is_active', 'is_featured', 'is_physical', 'tax_rate']
    search_fields = ['code', 'name', 'description', 'sku', 'barcode']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductAttributeValueInline]
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'slug', 'description', 'category')
        }),
        (_('Fiyat ve Vergi'), {
            'fields': ('price', 'cost', 'tax_rate', 'discount_price')
        }),
        (_('Stok ve Fiziksel Özellikler'), {
            'fields': ('stock', 'is_physical', 'weight', 'dimensions', 'sku', 'barcode')
        }),
        (_('Durum'), {
            'fields': ('status', 'is_featured', 'is_active')
        }),
    )


class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'previous_stock', 'new_stock', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'product__code', 'reference', 'notes']
    readonly_fields = ['previous_stock', 'new_stock']
    autocomplete_fields = ['product']
    fieldsets = (
        (None, {
            'fields': ('product', 'movement_type', 'quantity', 'unit_cost')
        }),
        (_('Detaylar'), {
            'fields': ('reference', 'notes', 'created_by')
        }),
        (_('Stok Bilgisi'), {
            'fields': ('previous_stock', 'new_stock'),
            'classes': ('collapse',),
        }),
    )


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(StockMovement, StockMovementAdmin)