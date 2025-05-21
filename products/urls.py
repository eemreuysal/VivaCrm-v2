"""
URL configuration for products app.
"""
from django.urls import path, include
from products.views import (
    # Category views
    CategoryListView, CategoryDetailView, CategoryCreateView, CategoryUpdateView, 
    CategoryDeleteView, export_categories,
    
    # Product views
    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    
    # Product Image views
    ProductImageCreateView, ProductImageDeleteView,
    
    # Product Attribute views
    ProductAttributeListView, ProductAttributeCreateView, ProductAttributeUpdateView,
    ProductAttributeDeleteView, ProductAttributeValueCreateView, ProductAttributeValueUpdateView,
    ProductAttributeValueDeleteView,
    
    # Stock Management views
    StockMovementListView, StockMovementCreateView, StockMovementDetailView,
    BulkStockAdjustmentView, movement_fields_view,
    
    # Excel views
    product_excel_export_view as excel_export,
    product_excel_import_view as excel_import,
    product_excel_template_view as excel_template,
)

app_name = "products"

urlpatterns = [
    # Category URLs
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/export/", export_categories, name="export_categories"),
    path("categories/new/", CategoryCreateView.as_view(), name="category-create"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"),
    path("categories/<slug:slug>/edit/", CategoryUpdateView.as_view(), name="category-update"),
    path("categories/<slug:slug>/delete/", CategoryDeleteView.as_view(), name="category-delete"),
    
    # Excel Import/Export URLs - Facade pattern implementasyonu
    path("excel/", include('products.urls_excel')),
    
    # Legacy Excel URLs (geriye uyumluluk için - deprecate edilecek)
    path("excel/export/", excel_export, name="export_products"),
    path("excel/import/", excel_import, name="product-import"),
    path("excel/template/", excel_template, name="generate-product-template"),

    # Product URLs
    path("", ProductListView.as_view(), name="product-list"),
    path("new/", ProductCreateView.as_view(), name="product-create"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("<slug:slug>/edit/", ProductUpdateView.as_view(), name="product-update"),
    path("<slug:slug>/delete/", ProductDeleteView.as_view(), name="product-delete"),
    
    # Product Image URLs
    path("<slug:slug>/images/new/", ProductImageCreateView.as_view(), name="product-image-create"),
    path("images/<int:pk>/delete/", ProductImageDeleteView.as_view(), name="product-image-delete"),
    
    # Product Attribute URLs
    path("attributes/", ProductAttributeListView.as_view(), name="attribute-list"),
    path("attributes/new/", ProductAttributeCreateView.as_view(), name="attribute-create"),
    path("attributes/<slug:slug>/edit/", ProductAttributeUpdateView.as_view(), name="attribute-update"),
    path("attributes/<slug:slug>/delete/", ProductAttributeDeleteView.as_view(), name="attribute-delete"),
    
    # Product Attribute Value URLs
    path("<slug:slug>/attributes/new/", ProductAttributeValueCreateView.as_view(), name="attribute-value-create"),
    path("attribute-values/<int:pk>/edit/", ProductAttributeValueUpdateView.as_view(), name="attribute-value-update"),
    path("attribute-values/<int:pk>/delete/", ProductAttributeValueDeleteView.as_view(), name="attribute-value-delete"),
    
    # Stock Management URLs
    path("stock/", StockMovementListView.as_view(), name="movement-list"),
    path("stock/new/", StockMovementCreateView.as_view(), name="movement-create"),
    path("stock/<int:pk>/", StockMovementDetailView.as_view(), name="movement-detail"),
    path("stock/bulk-adjust/", BulkStockAdjustmentView.as_view(), name="bulk-stock-adjustment"),
    path("stock/import/", BulkStockAdjustmentView.as_view(), name="stock-adjustment-import"),  # Temporary redirect to bulk adjustment view
    path("movement-fields/", movement_fields_view, name="movement-fields")
]