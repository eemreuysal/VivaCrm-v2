"""
Orders modülü view'ları - Modüler yapı için gerekli import işlemleri
"""
# Excel ile ilgili view'ları import et
from .excel import (
    OrderExcelImportView, OrderExcelImportResultsView,
    OrderExcelTemplateView, OrderExcelReportView,
    validate_excel_file
)

# Bu modül sadece modüler yapı kullanıldığında kullanılır.
# urls.py modül içindeki view'ları doğrudan import etmektedir.