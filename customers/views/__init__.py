"""
Customers uygulaması için tüm view'ları içe aktarır.
"""

# Customer views
from .customer.views import (
    CustomerListView,
    CustomerDetailView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDeleteView
)

# Address views
from .address.views import (
    AddressCreateView,
    AddressUpdateView,
    AddressDeleteView
)

# Contact views
from .contact.views import (
    ContactCreateView,
    ContactUpdateView,
    ContactDeleteView
)

# Excel views
from .excel import (
    CustomerExcelImportView,
    AddressExcelImportView,
    ExcelImportResultsView,
    CustomerExcelExportView,
    AddressExcelExportView,
    CustomerExcelTemplateView,
    AddressExcelTemplateView,
    validate_excel_file,
    # Function-based views
    customer_excel_import_view,
    address_excel_import_view,
    excel_import_results_view,
    customer_excel_export_view,
    address_excel_export_view,
    customer_excel_template_view,
    address_excel_template_view
)

# Tüm view sınıfları ve fonksiyonları buradan içe aktarılır.
# Bu sayede URL'lerde doğrudan 'from customers.views import X' şeklinde import yapılabilir.