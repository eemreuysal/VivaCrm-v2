"""
Customers uygulaması için URL yapılandırması.
Tüm URL'ler müşteriler, adresler, ilgili kişiler ve Excel işlemleri için tanımlanır.
"""
from django.urls import path

# Tüm view'ları doğrudan customers.views paketinden içe aktar
from customers.views import (
    # Ana view'lar
    CustomerListView, CustomerDetailView, CustomerCreateView, 
    CustomerUpdateView, CustomerDeleteView,
    
    # Adres view'ları
    AddressCreateView, AddressUpdateView, AddressDeleteView,
    
    # İlgili kişi view'ları
    ContactCreateView, ContactUpdateView, ContactDeleteView,
    
    # Excel view'ları
    CustomerExcelImportView, AddressExcelImportView,
    ExcelImportResultsView, CustomerExcelExportView,
    AddressExcelExportView, CustomerExcelTemplateView,
    AddressExcelTemplateView, validate_excel_file,
    
    # Function-based Excel view'ları
    customer_excel_import_view, address_excel_import_view,
    excel_import_results_view, customer_excel_export_view,
    address_excel_export_view, customer_excel_template_view,
    address_excel_template_view
)

app_name = "customers"

# Ana URL'ler - Müşteriler
urlpatterns = [
    # Müşteri listeleme ve detay sayfaları
    path("", CustomerListView.as_view(), name="customer-list"),
    path("new/", CustomerCreateView.as_view(), name="customer-create"),
    path("<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
    path("<int:pk>/edit/", CustomerUpdateView.as_view(), name="customer-update"),
    path("<int:pk>/delete/", CustomerDeleteView.as_view(), name="customer-delete"),
    
    # Adres işlemleri
    path("<int:customer_pk>/addresses/new/", AddressCreateView.as_view(), name="address-create"),
    path("addresses/<int:pk>/edit/", AddressUpdateView.as_view(), name="address-update"),
    path("addresses/<int:pk>/delete/", AddressDeleteView.as_view(), name="address-delete"),
    
    # İlgili kişi işlemleri
    path("<int:customer_pk>/contacts/new/", ContactCreateView.as_view(), name="contact-create"),
    path("contacts/<int:pk>/edit/", ContactUpdateView.as_view(), name="contact-update"),
    path("contacts/<int:pk>/delete/", ContactDeleteView.as_view(), name="contact-delete"),
]

# Excel işlemleri için URL'ler
excel_urlpatterns = [
    # Class-based view URLs
    path('excel/import/', CustomerExcelImportView.as_view(), name='excel-import'),
    path('excel/import/results/<str:session_id>/', ExcelImportResultsView.as_view(), name='excel-import-results'),
    path('excel/template/', CustomerExcelTemplateView.as_view(), name='customer-excel-template'),
    path('excel/export/', CustomerExcelExportView.as_view(), name='excel-export'),
    path('excel/validate/', validate_excel_file, name='excel-validate'),
    
    # Adres Excel
    path('address/excel/import/', AddressExcelImportView.as_view(), name='address-excel-import'),
    path('address/excel/import/results/<str:session_id>/', ExcelImportResultsView.as_view(), name='address-excel-import-results'),
    path('address/excel/template/', AddressExcelTemplateView.as_view(), name='address-excel-template'),
    path('address/excel/export/', AddressExcelExportView.as_view(), name='address-excel-export'),
    
    # Eski URL'ler (geriye uyumluluk için)
    path("export/", customer_excel_export_view, name="export_customers"),
    path("export/addresses/", address_excel_export_view, name="export_addresses"),
    path("import/", customer_excel_import_view, name="customer_import"),
    path("import/addresses/", address_excel_import_view, name="address_import"),
    path("template/", customer_excel_template_view, name="generate_customer_template"),
    path("template/addresses/", address_excel_template_view, name="generate_address_template"),
]

# Tüm URL'leri birleştir
urlpatterns += excel_urlpatterns