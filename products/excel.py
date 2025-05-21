"""
Products modülü Excel işlemleri için backward compatibility layer.
Yeni kod products.excel modülünü kullanmalı.
"""
import warnings
from .excel.manager import ProductExcelManager
from .excel.importer import ProductExcelImporter
from .excel.exporter import ProductExcelExporter

# Deprecation warning
warnings.warn(
    "products.excel modülü deprecate edilmiştir. "
    "Lütfen products.excel.manager.ProductExcelManager kullanın.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility için sınıfları export et
__all__ = [
    'ProductExcelManager',
    'ProductExcelImporter', 
    'ProductExcelExporter'
]

# Eski fonksiyon imzaları için wrapper'lar
def export_products_to_excel(queryset, include_all=True):
    """Deprecated: ProductExcelManager.export_products() kullanın"""
    manager = ProductExcelManager()
    return manager.export_products(queryset)

def import_products_from_excel(file_path, update_existing=True):
    """Deprecated: ProductExcelManager.import_products() kullanın"""
    manager = ProductExcelManager()
    return manager.import_products(file_path)