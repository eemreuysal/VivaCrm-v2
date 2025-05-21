"""
Views for the products app.
All views are organized into submodules by functionality.
"""
# Category-related views
from products.views.category import (
    CategoryListView,
    CategoryDetailView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    export_categories,
)

# Product-related views
from products.views.product import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

# Product image views
from products.views.image import (
    ProductImageCreateView,
    ProductImageDeleteView,
)

# Product attribute views
from products.views.attribute import (
    ProductAttributeListView,
    ProductAttributeCreateView,
    ProductAttributeUpdateView,
    ProductAttributeDeleteView,
    ProductAttributeValueCreateView,
    ProductAttributeValueUpdateView,
    ProductAttributeValueDeleteView,
)

# Stock management views
from products.views.stock import (
    StockMovementListView,
    StockMovementCreateView,
    StockMovementDetailView,
    BulkStockAdjustmentView,
    movement_fields_view,
)

# Excel views - These are already modular
from products.views.excel import (
    ProductExcelImportView,
    ProductExcelExportView,
    ProductExcelTemplateView,
    ProductExcelImportResultsView,
    product_excel_import_view,
    product_excel_export_view,
    product_excel_template_view,
    validate_excel_file,
    import_progress_api,
)

# Excel facades
from products.views.excel_facade import ExcelImportFacade, ExcelExportFacade

# Export all views
__all__ = [
    # Category views
    'CategoryListView',
    'CategoryDetailView',
    'CategoryCreateView',
    'CategoryUpdateView',
    'CategoryDeleteView',
    'export_categories',
    
    # Product views
    'ProductListView',
    'ProductDetailView',
    'ProductCreateView',
    'ProductUpdateView',
    'ProductDeleteView',
    
    # Image views
    'ProductImageCreateView',
    'ProductImageDeleteView',
    
    # Attribute views
    'ProductAttributeListView',
    'ProductAttributeCreateView',
    'ProductAttributeUpdateView',
    'ProductAttributeDeleteView',
    'ProductAttributeValueCreateView',
    'ProductAttributeValueUpdateView',
    'ProductAttributeValueDeleteView',
    
    # Stock views
    'StockMovementListView',
    'StockMovementCreateView',
    'StockMovementDetailView',
    'BulkStockAdjustmentView',
    'movement_fields_view',
    
    # Excel views
    'ProductExcelImportView',
    'ProductExcelExportView',
    'ProductExcelTemplateView',
    'ProductExcelImportResultsView',
    'product_excel_import_view',
    'product_excel_export_view',
    'product_excel_template_view',
    'validate_excel_file',
    'import_progress_api',
    
    # Excel facades
    'ExcelImportFacade',
    'ExcelExportFacade',
]