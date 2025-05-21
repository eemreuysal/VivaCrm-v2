# core/excel_reporting.py
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import logging

from django.db import transaction
from django.utils import timezone

from .models_import import ImportTask, ImportSummary, DetailedImportResult

logger = logging.getLogger(__name__)


class ImportReporter:
    """İçe aktarma işlemleri için detaylı raporlama sınıfı"""
    
    def __init__(self, import_task: ImportTask):
        self.import_task = import_task
        self.summary, _ = ImportSummary.objects.get_or_create(import_task=import_task)
        self.current_row = 0
        self.field_stats = defaultdict(lambda: {'success': 0, 'failed': 0})
        self.error_types = defaultdict(int)
        self.operation_counts = defaultdict(int)
        
    def start_import(self):
        """İçe aktarma işlemini başlat"""
        self.import_task.started_at = timezone.now()
        self.import_task.status = 'processing'
        self.import_task.save()
        
    def report_row(
        self,
        row_number: int,
        data: Dict[str, Any],
        status: str,
        fields_updated: Optional[List[str]] = None,
        fields_failed: Optional[Dict[str, str]] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        dependent_operations: Optional[Dict[str, Any]] = None
    ):
        """Tek bir satır için sonuç raporu"""
        
        # Detaylı sonuç kaydı oluştur
        detailed_result = DetailedImportResult.objects.create(
            import_task=self.import_task,
            row_number=row_number,
            data=data,
            status=status,
            fields_updated=fields_updated,
            fields_failed=fields_failed,
            error_message=error_message,
            error_details=error_details,
            dependent_operations=dependent_operations
        )
        
        # Özet istatistikleri güncelle
        self._update_summary_stats(status, fields_updated, fields_failed)
        
        # Alan başarı istatistiklerini güncelle
        if fields_updated:
            for field in fields_updated:
                self.field_stats[field]['success'] += 1
                
        if fields_failed:
            for field, error in fields_failed.items():
                self.field_stats[field]['failed'] += 1
                self.error_types[error] += 1
        
        # İşlem sayaçlarını güncelle
        self.operation_counts[status] += 1
        
        # İlerleme güncelle
        self.current_row = row_number
        self._update_progress()
        
        return detailed_result
    
    def report_batch(self, batch_results: List[Dict[str, Any]]):
        """Toplu sonuç raporu"""
        with transaction.atomic():
            for result in batch_results:
                self.report_row(**result)
    
    def complete_import(self):
        """İçe aktarma işlemini tamamla"""
        # Alan başarı oranlarını hesapla
        field_success_rates = {}
        for field, stats in self.field_stats.items():
            total = stats['success'] + stats['failed']
            if total > 0:
                field_success_rates[field] = {
                    'total': total,
                    'success': stats['success'],
                    'failed': stats['failed'],
                    'success_rate': (stats['success'] / total) * 100
                }
        
        # Hata özetini oluştur
        error_summary = {
            'error_types': dict(self.error_types),
            'most_common_errors': sorted(
                self.error_types.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
        
        # İşlem süresini hesapla
        processing_time = None
        if self.import_task.started_at:
            self.import_task.completed_at = timezone.now()
            processing_time = self.import_task.completed_at - self.import_task.started_at
        
        # Özeti güncelle
        with transaction.atomic():
            self.summary.field_success_rates = field_success_rates
            self.summary.error_summary = error_summary
            self.summary.processing_time = processing_time
            self.summary.save()
            
            # İçe aktarma görevini güncelle
            self.import_task.progress = 100
            self.import_task.update_status()
    
    def _update_summary_stats(self, status: str, fields_updated: List[str], fields_failed: Dict[str, str]):
        """Özet istatistikleri güncelle"""
        self.summary.total_rows += 1
        
        if status == 'created':
            self.summary.successful_rows += 1
            self.summary.created_count += 1
        elif status == 'updated':
            self.summary.successful_rows += 1
            self.summary.updated_count += 1
        elif status == 'skipped':
            self.summary.skipped_rows += 1
        elif status == 'failed':
            self.summary.failed_rows += 1
        elif status == 'partial':
            self.summary.partial_rows += 1
            # Kısmi başarılı satırlarda güncellenen alan sayısı
            if fields_updated:
                self.summary.updated_count += 1
    
    def _update_progress(self):
        """İlerleme yüzdesini güncelle"""
        if self.summary.total_rows > 0:
            progress = min(99, int((self.current_row / self.summary.total_rows) * 100))
            self.import_task.progress = progress
            self.import_task.current_row = self.current_row
            self.import_task.save(update_fields=['progress', 'current_row'])
    
    def get_report(self) -> Dict[str, Any]:
        """Detaylı rapor oluştur"""
        # Özet bilgilerini yenile
        self.summary.refresh_from_db()
        
        # Başarı dağılımı
        success_distribution = {
            'Başarılı': self.summary.successful_rows,
            'Başarısız': self.summary.failed_rows,
            'Kısmi Başarılı': self.summary.partial_rows,
            'Atlandı': self.summary.skipped_rows
        }
        
        # İşlem dağılımı
        operation_distribution = {
            'Oluşturulan': self.summary.created_count,
            'Güncellenen': self.summary.updated_count
        }
        
        # En yaygın hatalar
        most_common_errors = []
        if self.summary.error_summary and 'most_common_errors' in self.summary.error_summary:
            most_common_errors = self.summary.error_summary['most_common_errors']
        
        # Alan başına başarı oranları
        field_performance = []
        if self.summary.field_success_rates:
            for field, stats in self.summary.field_success_rates.items():
                field_performance.append({
                    'field': field,
                    'total': stats['total'],
                    'success': stats['success'],
                    'failed': stats['failed'],
                    'success_rate': stats['success_rate']
                })
        
        # Genel rapor
        report = {
            'summary': {
                'total_rows': self.summary.total_rows,
                'success_rate': self.summary.success_rate,
                'partial_success_rate': self.summary.partial_success_rate,
                'processing_time': str(self.summary.processing_time) if self.summary.processing_time else None,
            },
            'distributions': {
                'success': success_distribution,
                'operations': operation_distribution
            },
            'field_performance': sorted(
                field_performance, 
                key=lambda x: x['success_rate'], 
                reverse=True
            ),
            'errors': {
                'total_errors': self.summary.failed_rows,
                'most_common': most_common_errors
            },
            'detailed_results': {
                'total': self.import_task.detailed_results.count(),
                'by_status': dict(
                    self.import_task.detailed_results.values('status')
                    .annotate(count=models.Count('id'))
                    .values_list('status', 'count')
                )
            }
        }
        
        return report
    
    @classmethod
    def get_task_report(cls, import_task_id: int) -> Dict[str, Any]:
        """Belirli bir görev için rapor al"""
        try:
            import_task = ImportTask.objects.get(id=import_task_id)
            reporter = cls(import_task)
            return reporter.get_report()
        except ImportTask.DoesNotExist:
            return {'error': 'İçe aktarma görevi bulunamadı'}
    
    def export_detailed_report(self) -> List[Dict[str, Any]]:
        """Detaylı sonuçları dışa aktar"""
        detailed_results = []
        
        for result in self.import_task.detailed_results.all():
            detailed_results.append({
                'row_number': result.row_number,
                'status': result.get_status_display(),
                'data': result.data,
                'fields_updated': result.fields_updated,
                'fields_failed': result.fields_failed,
                'error_message': result.error_message,
                'error_details': result.error_details,
                'dependent_operations': result.dependent_operations,
                'created_at': result.created_at.isoformat()
            })
        
        return detailed_results