"""
Excel error handling system with correctable/non-correctable error classification
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ErrorSeverity(Enum):
    """Hata ciddiyet seviyeleri"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorType(Enum):
    """Hata türleri"""
    MISSING_FIELD = "missing_field"
    INVALID_FORMAT = "invalid_format"
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    DUPLICATE_VALUE = "duplicate_value"
    FOREIGN_KEY_ERROR = "foreign_key_error"
    BUSINESS_RULE_ERROR = "business_rule_error"
    SYSTEM_ERROR = "system_error"


@dataclass
class ErrorDefinition:
    """Hata tanımı"""
    type: ErrorType
    message: str
    severity: ErrorSeverity
    is_correctable: bool = False
    correction_hint: Optional[str] = None
    validation_pattern: Optional[str] = None
    auto_correction_available: bool = False


class BaseError(Exception):
    """Temel hata sınıfı"""
    def __init__(self, message: str, row: Optional[int] = None, 
                 column: Optional[str] = None, value: Any = None,
                 correction_suggestion: Optional[str] = None):
        self.message = message
        self.row = row
        self.column = column
        self.value = value
        self.correction_suggestion = correction_suggestion
        super().__init__(message)


class CorrectableError(BaseError):
    """Düzeltilebilir hata"""
    def __init__(self, message: str, row: Optional[int] = None,
                 column: Optional[str] = None, value: Any = None,
                 correction_suggestion: Optional[str] = None,
                 auto_correctable: bool = False):
        super().__init__(message, row, column, value, correction_suggestion)
        self.auto_correctable = auto_correctable


class NonCorrectableError(BaseError):
    """Düzeltilemeyen hata"""
    pass


# Hata tanımlamaları
ERROR_DEFINITIONS = {
    # Düzeltilebilir hatalar
    "price_format": ErrorDefinition(
        type=ErrorType.INVALID_FORMAT,
        message="Fiyat formatı hatalı",
        severity=ErrorSeverity.WARNING,
        is_correctable=True,
        correction_hint="Virgül yerine nokta kullanın veya sayısal değer girin",
        validation_pattern=r"^\d+([.,]\d{1,2})?$",
        auto_correction_available=True
    ),
    
    "date_format": ErrorDefinition(
        type=ErrorType.INVALID_FORMAT,
        message="Tarih formatı hatalı",
        severity=ErrorSeverity.WARNING,
        is_correctable=True,
        correction_hint="DD/MM/YYYY veya DD.MM.YYYY formatında girin",
        validation_pattern=r"^\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4}$",
        auto_correction_available=True
    ),
    
    "sku_format": ErrorDefinition(
        type=ErrorType.INVALID_FORMAT,
        message="SKU formatı hatalı",
        severity=ErrorSeverity.WARNING,
        is_correctable=True,
        correction_hint="Boşlukları kaldırın ve özel karakterleri düzeltin",
        validation_pattern=r"^[A-Za-z0-9\-_]+$",
        auto_correction_available=True
    ),
    
    # Kategori hatası kaldırıldı - artık otomatik oluşturuluyor
    
    "invalid_stock": ErrorDefinition(
        type=ErrorType.INVALID_VALUE,
        message="Stok değeri hatalı",
        severity=ErrorSeverity.WARNING,
        is_correctable=True,
        correction_hint="Pozitif tam sayı girin",
        validation_pattern=r"^\d+$",
        auto_correction_available=True
    ),
    
    # Düzeltilemeyen hatalar
    "missing_required": ErrorDefinition(
        type=ErrorType.MISSING_FIELD,
        message="Zorunlu alan eksik",
        severity=ErrorSeverity.ERROR,
        is_correctable=False
    ),
    
    "duplicate_sku": ErrorDefinition(
        type=ErrorType.DUPLICATE_VALUE,
        message="Bu SKU zaten mevcut",
        severity=ErrorSeverity.ERROR,
        is_correctable=False
    ),
    
    "invalid_tax_rate": ErrorDefinition(
        type=ErrorType.INVALID_VALUE,
        message="Geçersiz KDV oranı",
        severity=ErrorSeverity.ERROR,
        is_correctable=False,
        correction_hint="Geçerli KDV oranları: %1, %8, %18"
    ),
    
    "system_error": ErrorDefinition(
        type=ErrorType.SYSTEM_ERROR,
        message="Sistem hatası",
        severity=ErrorSeverity.CRITICAL,
        is_correctable=False
    ),
    
    "required_field": ErrorDefinition(
        type=ErrorType.MISSING_FIELD,
        message="Bu alan gereklidir",
        severity=ErrorSeverity.ERROR,
        is_correctable=False
    ),
    
    "MISSING_COLUMN": ErrorDefinition(
        type=ErrorType.MISSING_FIELD,
        message="Gerekli sütun bulunamadı",
        severity=ErrorSeverity.ERROR,
        is_correctable=False
    )
}


class ExcelErrorHandler:
    """Excel hata yönetimi"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.correctable_errors: List[Dict[str, Any]] = []
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Return all errors as a list"""
        return self.errors
    
    def to_pandas_errors(self) -> List[Dict[str, Any]]:
        """Return errors in a format suitable for pandas DataFrame"""
        return self.errors
        
    def add_error(self, error_key: str, row: int, column: str, 
                  value: Any, extra_data: Optional[Dict] = None) -> None:
        """Hata ekle"""
        error_def = ERROR_DEFINITIONS.get(error_key)
        if not error_def:
            error_def = ERROR_DEFINITIONS["system_error"]
            
        error_data = {
            "row": row,
            "column": column,
            "value": value,
            "error_key": error_key,
            "message": error_def.message,
            "severity": error_def.severity.value,
            "is_correctable": error_def.is_correctable,
            "correction_hint": error_def.correction_hint,
            "auto_correction_available": error_def.auto_correction_available,
            "timestamp": datetime.now().isoformat()
        }
        
        if extra_data:
            error_data.update(extra_data)
            
        if error_def.severity == ErrorSeverity.WARNING:
            self.warnings.append(error_data)
        else:
            self.errors.append(error_data)
            
        if error_def.is_correctable:
            self.correctable_errors.append(error_data)
            
    def get_summary(self) -> Dict[str, Any]:
        """Hata özeti"""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "correctable_errors": len(self.correctable_errors),
            "error_breakdown": self._get_error_breakdown(),
            "can_continue": len(self.errors) == 0
        }
        
    def _get_error_breakdown(self) -> Dict[str, int]:
        """Hata türlerine göre dağılım"""
        breakdown = {}
        for error in self.errors + self.warnings:
            error_key = error["error_key"]
            breakdown[error_key] = breakdown.get(error_key, 0) + 1
        return breakdown
        
    def get_correctable_errors_by_type(self) -> Dict[str, List[Dict]]:
        """Düzeltilebilir hataları türe göre grupla"""
        grouped = {}
        for error in self.correctable_errors:
            error_key = error["error_key"]
            if error_key not in grouped:
                grouped[error_key] = []
            grouped[error_key].append(error)
        return grouped
        
    def has_critical_errors(self) -> bool:
        """Kritik hata var mı?"""
        return any(e["severity"] == ErrorSeverity.CRITICAL.value for e in self.errors)
        
    def clear(self) -> None:
        """Hataları temizle"""
        self.errors.clear()
        self.warnings.clear()
        self.correctable_errors.clear()