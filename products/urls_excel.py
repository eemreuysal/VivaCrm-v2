"""
Products Excel URL yapılandırması.
Facade pattern implementasyonu ile yenilenmiş Excel view'ları için URL'ler.
"""
from django.urls import path
from products.views import (
    ProductExcelImportView,
    ProductExcelExportView,
    ProductExcelTemplateView,
    ProductExcelImportResultsView,
    validate_excel_file,
    import_progress_api
)

urlpatterns = [
    # Excel import/export
    path('import/', ProductExcelImportView.as_view(), name='excel-import'),
    path('import/results/<str:session_id>/', ProductExcelImportResultsView.as_view(), name='excel-import-results'),
    path('export/', ProductExcelExportView.as_view(), name='excel-export'),
    path('template/', ProductExcelTemplateView.as_view(), name='excel-template'),
    
    # AJAX endpoints
    path('validate/', validate_excel_file, name='excel-validate'),
    path('progress/<str:session_id>/', import_progress_api, name='excel-progress'),
]