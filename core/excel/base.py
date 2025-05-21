"""
Excel import/export işlemleri için base sınıflar.
Tüm modül-spesifik Excel işlemleri bu sınıfları extend etmelidir.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from io import BytesIO
from django.db import models, transaction
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class BaseExcelImporter(ABC):
    """
    Tüm Excel importer'ları için base class.
    Single Responsibility Principle: Sadece import işlemlerinden sorumlu.
    """
    
    def __init__(self, model_class: models.Model):
        self.model_class = model_class
        self.errors: List[Dict[str, Any]] = []
        self.successes: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.row_count = 0
        
    @abstractmethod
    def get_field_mapping(self) -> Dict[str, str]:
        """Excel başlıklarını model field'larına map'le"""
        pass
    
    @abstractmethod
    def validate_row(self, row_data: Dict[str, Any], row_index: int) -> bool:
        """Tek bir satırı doğrula"""
        pass
    
    @abstractmethod
    def process_row(self, row_data: Dict[str, Any], row_index: int) -> Optional[models.Model]:
        """Tek bir satırı işle ve model instance döndür"""
        pass
    
    def import_data(self, file_path: str, **options) -> Dict[str, Any]:
        """
        Ana import metodu.
        Template Method Pattern: Alt sınıflar detayları implemente eder.
        """
        try:
            # Excel dosyasını oku
            df = self._read_excel_file(file_path, **options)
            
            # Field mapping uygula
            df = self._apply_field_mapping(df)
            
            # Satırları işle
            self._process_dataframe(df, **options)
            
            return self._generate_import_result()
            
        except Exception as e:
            logger.error(f"Excel import hatası: {str(e)}")
            raise
    
    def _read_excel_file(self, file_path: str, **options) -> pd.DataFrame:
        """Excel dosyasını oku ve DataFrame döndür"""
        sheet_name = options.get('sheet_name', 0)
        skiprows = options.get('skiprows', 0)
        
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)
        except Exception as e:
            raise ValidationError(f"Excel dosyası okunamadı: {str(e)}")
    
    def _apply_field_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Field mapping'i DataFrame'e uygula"""
        field_mapping = self.get_field_mapping()
        
        # Mevcut kolonları kontrol et
        missing_columns = set(field_mapping.keys()) - set(df.columns)
        if missing_columns:
            self.warnings.append({
                'message': f"Eksik kolonlar: {', '.join(missing_columns)}"
            })
        
        # Kolon isimlerini değiştir
        df = df.rename(columns=field_mapping)
        return df
    
    def _process_dataframe(self, df: pd.DataFrame, **options):
        """DataFrame'deki tüm satırları işle"""
        batch_size = options.get('batch_size', 100)
        use_transaction = options.get('use_transaction', True)
        
        self.row_count = len(df)
        
        for index, row in df.iterrows():
            row_data = row.to_dict()
            row_index = index + 1  # Excel satır numarası için
            
            try:
                # Satırı doğrula
                if not self.validate_row(row_data, row_index):
                    continue
                
                # Satırı işle
                if use_transaction:
                    with transaction.atomic():
                        instance = self.process_row(row_data, row_index)
                else:
                    instance = self.process_row(row_data, row_index)
                
                if instance:
                    self.successes.append({
                        'row': row_index,
                        'instance': instance,
                        'data': row_data
                    })
                    
            except ValidationError as e:
                self.errors.append({
                    'row': row_index,
                    'error': str(e),
                    'field': getattr(e, 'field', 'unknown'),
                    'data': row_data
                })
            except Exception as e:
                self.errors.append({
                    'row': row_index,
                    'error': str(e),
                    'type': type(e).__name__,
                    'data': row_data
                })
    
    def _generate_import_result(self) -> Dict[str, Any]:
        """Import sonuçlarını döndür"""
        return {
            'total_rows': self.row_count,
            'success_count': len(self.successes),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'successes': self.successes,
            'errors': self.errors,
            'warnings': self.warnings,
            'success_rate': (len(self.successes) / self.row_count * 100) if self.row_count > 0 else 0
        }


class BaseExcelExporter(ABC):
    """
    Tüm Excel exporter'ları için base class.
    Single Responsibility Principle: Sadece export işlemlerinden sorumlu.
    """
    
    def __init__(self, model_class: models.Model):
        self.model_class = model_class
        
    @abstractmethod
    def get_export_fields(self) -> List[str]:
        """Export edilecek field'ların listesi"""
        pass
    
    @abstractmethod
    def get_field_headers(self) -> Dict[str, str]:
        """Field isimlerini Excel başlıklarına map'le"""
        pass
    
    def export_data(self, queryset, **options) -> bytes:
        """
        Ana export metodu.
        Strategy Pattern: Alt sınıflar export stratejisini belirler.
        """
        # Export field'larını al
        fields = self.get_export_fields()
        headers = self.get_field_headers()
        
        # QuerySet'i optimize et
        queryset = self._optimize_queryset(queryset, fields)
        
        # DataFrame oluştur
        df = self._create_dataframe(queryset, fields)
        
        # Başlıkları uygula
        df = self._apply_headers(df, headers)
        
        # Excel'e dönüştür
        return self._convert_to_excel(df, **options)
    
    def _optimize_queryset(self, queryset, fields: List[str]):
        """QuerySet'i optimize et (select_related, prefetch_related)"""
        # Alt sınıflar override edebilir
        return queryset
    
    def _create_dataframe(self, queryset, fields: List[str]) -> pd.DataFrame:
        """QuerySet'ten DataFrame oluştur"""
        data = []
        
        for obj in queryset:
            row_data = {}
            for field in fields:
                # Nested field'ları destekle (örn: category__name)
                if '__' in field:
                    value = self._get_nested_value(obj, field)
                else:
                    value = getattr(obj, field, None)
                
                # Değeri formatla
                row_data[field] = self._format_value(value)
            
            data.append(row_data)
        
        return pd.DataFrame(data)
    
    def _get_nested_value(self, obj, field_path: str):
        """Nested field değerini al (örn: category__name)"""
        parts = field_path.split('__')
        value = obj
        
        for part in parts:
            if value is None:
                return None
            value = getattr(value, part, None)
        
        return value
    
    def _format_value(self, value):
        """Değeri Excel için formatla"""
        if pd.isna(value) or value is None:
            return ''
        return value
    
    def _apply_headers(self, df: pd.DataFrame, headers: Dict[str, str]) -> pd.DataFrame:
        """DataFrame kolonlarını başlıklara dönüştür"""
        return df.rename(columns=headers)
    
    def _convert_to_excel(self, df: pd.DataFrame, **options) -> bytes:
        """DataFrame'i Excel dosyasına dönüştür"""
        output = BytesIO()
        
        # Excel writer oluştur
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            sheet_name = options.get('sheet_name', 'Sheet1')
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Opsiyonel: Formatting uygula
            if hasattr(self, 'apply_formatting'):
                worksheet = writer.sheets[sheet_name]
                self.apply_formatting(worksheet)
        
        output.seek(0)
        return output.getvalue()
    
    def generate_template(self, **options) -> bytes:
        """Boş Excel template oluştur"""
        headers = self.get_field_headers()
        df = pd.DataFrame(columns=headers.values())
        
        return self._convert_to_excel(df, **options)