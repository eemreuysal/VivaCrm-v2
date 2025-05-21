"""
Excel işlemleri için özel exception sınıfları.
Clean Code: Spesifik hatalar için spesifik exception'lar.
"""


class ExcelError(Exception):
    """Excel işlemleri için base exception sınıfı"""
    pass


class ExcelImportError(ExcelError):
    """Import işlemleri sırasında oluşan hatalar"""
    def __init__(self, message: str, row: int = None, field: str = None):
        self.row = row
        self.field = field
        super().__init__(message)


class ExcelExportError(ExcelError):
    """Export işlemleri sırasında oluşan hatalar"""
    pass


class ValidationError(ExcelImportError):
    """Veri doğrulama hataları"""
    pass


class CategoryNotFoundError(ExcelImportError):
    """Kategori bulunamadığında"""
    pass


class ProductFamilyNotFoundError(ExcelImportError):
    """Ürün ailesi bulunamadığında"""
    pass


class InvalidPriceError(ValidationError):
    """Geçersiz fiyat değeri"""
    pass


class InvalidStockError(ValidationError):
    """Geçersiz stok değeri"""
    pass


class DuplicateEntryError(ExcelImportError):
    """Duplicate kayıt hatası"""
    def __init__(self, message: str, duplicate_field: str, duplicate_value: str, **kwargs):
        self.duplicate_field = duplicate_field
        self.duplicate_value = duplicate_value
        super().__init__(message, **kwargs)


class FileSizeError(ExcelError):
    """Dosya boyutu limiti aşıldığında"""
    def __init__(self, message: str, max_size: int, actual_size: int):
        self.max_size = max_size
        self.actual_size = actual_size
        super().__init__(message)


class UnsupportedFileTypeError(ExcelError):
    """Desteklenmeyen dosya tipi"""
    def __init__(self, message: str, file_type: str, supported_types: list):
        self.file_type = file_type
        self.supported_types = supported_types
        super().__init__(message)