# core/excel_result.py
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from .excel_reporting import ImportReporter
from .models_import import ImportTask


@dataclass
class ImportResult:
    """Excel import sonuç sınıfı"""
    success: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    details: List[Dict] = field(default_factory=list)
    created_ids: List[int] = field(default_factory=list)
    updated_ids: List[int] = field(default_factory=list)
    skipped_rows: List[int] = field(default_factory=list)
    validation_errors: Dict[int, List[str]] = field(default_factory=dict)
    partial_success_rows: List[int] = field(default_factory=list)
    field_level_results: Dict[int, Dict[str, bool]] = field(default_factory=dict)
    import_task: Optional[ImportTask] = None
    reporter: Optional[ImportReporter] = None
    
    @property
    def total(self) -> int:
        return self.success + self.failed + len(self.partial_success_rows)
    
    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0
        return (self.success / self.total) * 100
    
    @property
    def partial_success_rate(self) -> float:
        if self.total == 0:
            return 0
        return ((self.success + len(self.partial_success_rows)) / self.total) * 100
    
    def initialize_reporter(self, import_task: ImportTask):
        """Raporlayıcıyı başlat"""
        self.import_task = import_task
        self.reporter = ImportReporter(import_task)
        self.reporter.start_import()
    
    def add_error(self, row_num: int, error: str, data: Dict = None):
        """Hata ekle"""
        self.failed += 1
        self.errors.append(f"Satır {row_num}: {error}")
        
        if self.reporter and data:
            self.reporter.report_row(
                row_number=row_num,
                data=data,
                status='failed',
                error_message=error
            )
        
    def add_validation_error(self, row_num: int, field: str, error: str):
        """Validasyon hatası ekle"""
        if row_num not in self.validation_errors:
            self.validation_errors[row_num] = []
        self.validation_errors[row_num].append(f"{field}: {error}")
        
    def add_success(self, row_num: int, instance_id: int = None, 
                   is_created: bool = True, data: Dict = None, 
                   fields_updated: List[str] = None):
        """Başarılı kayıt ekle"""
        self.success += 1
        if instance_id:
            if is_created:
                self.created_ids.append(instance_id)
            else:
                self.updated_ids.append(instance_id)
                
        if self.reporter and data:
            self.reporter.report_row(
                row_number=row_num,
                data=data,
                status='created' if is_created else 'updated',
                fields_updated=fields_updated
            )
    
    def add_partial_success(self, row_num: int, fields_succeeded: Dict[str, bool], 
                          fields_failed: Dict[str, str], data: Dict = None,
                          instance_id: int = None):
        """Kısmi başarılı kayıt ekle"""
        self.partial_success_rows.append(row_num)
        self.field_level_results[row_num] = fields_succeeded
        
        if self.reporter and data:
            succeeded_fields = [f for f, success in fields_succeeded.items() if success]
            self.reporter.report_row(
                row_number=row_num,
                data=data,
                status='partial',
                fields_updated=succeeded_fields,
                fields_failed=fields_failed
            )
                
    def skip_row(self, row_num: int, reason: str = None, data: Dict = None):
        """Satırı atla"""
        self.skipped_rows.append(row_num)
        if reason:
            self.details.append({
                'row': row_num,
                'action': 'skipped',
                'reason': reason
            })
            
        if self.reporter and data:
            self.reporter.report_row(
                row_number=row_num,
                data=data,
                status='skipped',
                error_message=reason
            )
    
    def finalize(self):
        """İçe aktarmayı sonlandır"""
        if self.reporter:
            self.reporter.complete_import()
            return self.reporter.get_report()
            
    def to_dict(self) -> Dict:
        """Sonuçları sözlük olarak döndür"""
        return {
            'created': len(self.created_ids),
            'updated': len(self.updated_ids),
            'failed': self.failed,
            'partial': len(self.partial_success_rows),
            'skipped': len(self.skipped_rows),
            'total': self.total,
            'success_rate': self.success_rate,
            'partial_success_rate': self.partial_success_rate,
            'errors': self.errors,
            'validation_errors': self.validation_errors,
            'details': self.details
        }