from django.urls import path
from . import views
from . import views_excel

app_name = "products"

urlpatterns = [
    # Category URLs
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category-create"),
    path("categories/<slug:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("categories/<slug:slug>/edit/", views.CategoryUpdateView.as_view(), name="category-update"),
    path("categories/<slug:slug>/delete/", views.CategoryDeleteView.as_view(), name="category-delete"),
    
    # Product URLs
    path("", views.ProductListView.as_view(), name="product-list"),
    path("new/", views.ProductCreateView.as_view(), name="product-create"),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("<slug:slug>/edit/", views.ProductUpdateView.as_view(), name="product-update"),
    path("<slug:slug>/delete/", views.ProductDeleteView.as_view(), name="product-delete"),
    
    # Product Image URLs
    path("<slug:slug>/images/new/", views.ProductImageCreateView.as_view(), name="product-image-create"),
    path("images/<int:pk>/delete/", views.ProductImageDeleteView.as_view(), name="product-image-delete"),
    
    # Product Attribute URLs
    path("attributes/", views.ProductAttributeListView.as_view(), name="attribute-list"),
    path("attributes/new/", views.ProductAttributeCreateView.as_view(), name="attribute-create"),
    path("attributes/<slug:slug>/edit/", views.ProductAttributeUpdateView.as_view(), name="attribute-update"),
    path("attributes/<slug:slug>/delete/", views.ProductAttributeDeleteView.as_view(), name="attribute-delete"),
    
    # Product Attribute Value URLs
    path("<slug:slug>/attributes/new/", views.ProductAttributeValueCreateView.as_view(), name="attribute-value-create"),
    path("attribute-values/<int:pk>/edit/", views.ProductAttributeValueUpdateView.as_view(), name="attribute-value-update"),
    path("attribute-values/<int:pk>/delete/", views.ProductAttributeValueDeleteView.as_view(), name="attribute-value-delete"),
    
    # Stock Management URLs
    path("stock/", views.StockMovementListView.as_view(), name="movement-list"),
    path("stock/new/", views.StockMovementCreateView.as_view(), name="movement-create"),
    path("stock/<int:pk>/", views.StockMovementDetailView.as_view(), name="movement-detail"),
    path("stock/bulk-adjust/", views.BulkStockAdjustmentView.as_view(), name="bulk-stock-adjustment"),
    path("movement-fields/", views.movement_fields_view, name="movement-fields"),
    
    # Excel Import/Export URLs
    path("export/", views_excel.export_products, name="export_products"),
    path("export/stock/", views_excel.export_stock, name="export_stock"),
    path("import/", views_excel.ProductImportView.as_view(), name="product_import"),
    path("import/stock/", views_excel.StockAdjustmentImportView.as_view(), name="stock_adjustment_import"),
    path("template/", views_excel.generate_product_template, name="generate_product_template"),
    path("template/stock/", views_excel.generate_stock_template, name="generate_stock_template"),
]