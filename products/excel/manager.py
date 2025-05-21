"""
Product Excel işlemlerini yöneten facade sınıfı.
Facade Pattern: Karmaşık alt sistemlere basit bir arayüz sağlar.
"""
from typing import Optional, Dict, Any, Union
from pathlib import Path
import logging

from .importer import ProductExcelImporter
from .exporter import ProductExcelExporter
from core.excel.chunked import ChunkedExcelReader, MemoryEfficientExcelWriter
from core.excel.exceptions import ExcelError

logger = logging.getLogger(__name__)


class ProductExcelManager:
    """
    Ürün Excel işlemlerini yöneten ana sınıf.
    Import, export ve diğer Excel işlemlerini tek bir noktadan yönetir.
    """
    
    def __init__(self):
        self.importer = ProductExcelImporter()
        self.exporter = ProductExcelExporter()
        
    def import_products(
        self,
        file_path: Union[str, Path],
        use_chunks: bool = False,
        chunk_size: int = 1000,
        **options
    ) -> Dict[str, Any]:
        """
        Ürünleri Excel dosyasından import et.
        
        Args:
            file_path: Excel dosya yolu
            use_chunks: Büyük dosyalar için chunk kullan
            chunk_size: Chunk boyutu
            **options: Ek seçenekler
            
        Returns:
            Import sonuçları
        """
        try:
            file_path = Path(file_path)
            
            # Dosya boyutuna göre chunk kullanımını otomatik belirle
            if use_chunks or self._should_use_chunks(file_path):
                logger.info(f"Chunk mode ile import başlatılıyor: {file_path}")
                return self._import_with_chunks(file_path, chunk_size, **options)
            else:
                logger.info(f"Normal import başlatılıyor: {file_path}")
                return self.importer.import_data(str(file_path), **options)
                
        except ExcelError as e:
            logger.error(f"Excel import hatası: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Beklenmeyen import hatası: {str(e)}")
            raise ExcelError(f"Import işlemi başarısız: {str(e)}")
    
    def export_products(
        self,
        queryset,
        export_type: str = 'full',
        use_chunks: bool = False,
        chunk_size: int = 5000,
        **options
    ) -> bytes:
        """
        Ürünleri Excel dosyasına export et.
        
        Args:
            queryset: Export edilecek ürünler
            export_type: Export tipi ('full', 'price_list', 'inventory', 'stock_info')
            use_chunks: Büyük veri setleri için chunk kullan
            chunk_size: Chunk boyutu
            **options: Ek seçenekler
            
        Returns:
            Excel dosya içeriği (bytes)
        """
        try:
            # Export tipine göre uygun metodu çağır
            if export_type == 'price_list':
                return self.exporter.export_price_list(queryset, **options)
            elif export_type == 'inventory':
                return self.exporter.export_inventory_report(queryset, **options)
            elif export_type == 'stock_info':
                return self.exporter.export_with_stock_info(queryset, **options)
            else:
                # Büyük veri setleri için chunk export
                if use_chunks or queryset.count() > 10000:
                    return self._export_with_chunks(queryset, chunk_size, **options)
                else:
                    return self.exporter.export_data(queryset, **options)
                    
        except Exception as e:
            logger.error(f"Export hatası: {str(e)}")
            raise ExcelError(f"Export işlemi başarısız: {str(e)}")
    
    def generate_import_template(self, **options) -> bytes:
        """Import için boş Excel template oluştur"""
        return self.exporter.generate_template(**options)
    
    def validate_import_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Import dosyasını önceden doğrula.
        Hataları erken tespit etmek için kullanılır.
        """
        try:
            file_path = Path(file_path)
            
            # Dosya kontrolü
            if not file_path.exists():
                return {
                    'valid': False,
                    'errors': ['Dosya bulunamadı']
                }
            
            # Boyut kontrolü
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB
                return {
                    'valid': False,
                    'errors': ['Dosya boyutu çok büyük (max 100MB)']
                }
            
            # İçerik kontrolü
            reader = ChunkedExcelReader(file_path, chunk_size=100)
            headers_valid = True
            errors = []
            
            # İlk chunk'ı okuyup başlıkları kontrol et
            for i, chunk in enumerate(reader.read_chunks()):
                if i == 0:  # İlk chunk
                    required_headers = set(self.importer.get_field_mapping().keys())
                    actual_headers = set(chunk.columns.tolist())
                    missing_headers = required_headers - actual_headers
                    
                    if missing_headers:
                        headers_valid = False
                        errors.append(f"Eksik başlıklar: {', '.join(missing_headers)}")
                
                break  # Sadece ilk chunk'ı kontrol et
            
            return {
                'valid': headers_valid and not errors,
                'errors': errors,
                'file_size': file_size,
                'estimated_rows': self._estimate_row_count(file_path)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [str(e)]
            }
    
    def _should_use_chunks(self, file_path: Path) -> bool:
        """Dosya boyutuna göre chunk kullanımını belirle"""
        # 10MB'dan büyük dosyalar için chunk kullan
        return file_path.stat().st_size > 10 * 1024 * 1024
    
    def _estimate_row_count(self, file_path: Path) -> int:
        """Dosyadaki tahmini satır sayısını hesapla"""
        # Basit tahmin: dosya boyutu / ortalama satır boyutu
        file_size = file_path.stat().st_size
        avg_row_size = 500  # Tahmini ortalama satır boyutu (byte)
        return file_size // avg_row_size
    
    def _import_with_chunks(
        self,
        file_path: Path,
        chunk_size: int,
        **options
    ) -> Dict[str, Any]:
        """Chunk kullanarak import yap"""
        reader = ChunkedExcelReader(file_path, chunk_size=chunk_size)
        
        total_results = {
            'total_rows': 0,
            'success_count': 0,
            'error_count': 0,
            'warning_count': 0,
            'successes': [],
            'errors': [],
            'warnings': []
        }
        
        def process_chunk(df_chunk, chunk_index):
            """Her chunk'ı işle"""
            # DataFrame'i dict'lere dönüştür
            chunk_data = df_chunk.to_dict('records')
            
            # Her satırı import et
            chunk_results = {
                'errors': [],
                'warnings': []
            }
            
            for i, row_data in enumerate(chunk_data):
                row_index = chunk_index * chunk_size + i + 1
                
                try:
                    # Field mapping uygula
                    mapped_data = {}
                    field_mapping = self.importer.get_field_mapping()
                    
                    for excel_header, model_field in field_mapping.items():
                        if excel_header in row_data:
                            mapped_data[model_field] = row_data[excel_header]
                    
                    # Validasyon ve işleme
                    if self.importer.validate_row(mapped_data, row_index):
                        instance = self.importer.process_row(mapped_data, row_index)
                        if instance:
                            total_results['success_count'] += 1
                            
                except Exception as e:
                    chunk_results['errors'].append({
                        'row': row_index,
                        'error': str(e)
                    })
            
            return chunk_results
        
        # Chunk'ları işle
        result = reader.process_file(process_chunk, **options)
        
        # Sonuçları birleştir
        total_results['total_rows'] = result['total_rows']
        total_results['errors'] = result['errors']
        total_results['warnings'] = result.get('warnings', [])
        total_results['warning_count'] = len(total_results['warnings'])
        total_results['error_count'] = len(total_results['errors'])
        
        return total_results
    
    def _export_with_chunks(
        self,
        queryset,
        chunk_size: int,
        **options
    ) -> bytes:
        """Chunk kullanarak export yap"""
        from django.core.paginator import Paginator
        import pandas as pd
        from io import BytesIO
        
        # Paginator ile chunk'lara böl
        paginator = Paginator(queryset, chunk_size)
        
        # Geçici dosya oluştur
        output = BytesIO()
        
        def chunk_generator():
            """QuerySet'i DataFrame chunk'larına dönüştür"""
            for page_num in paginator.page_range:
                page = paginator.page(page_num)
                
                # QuerySet'i DataFrame'e dönüştür
                data = []
                fields = self.exporter.get_export_fields()
                
                for obj in page.object_list:
                    row_data = {}
                    for field in fields:
                        if '__' in field:
                            value = self.exporter._get_nested_value(obj, field)
                        else:
                            value = getattr(obj, field, None)
                        row_data[field] = self.exporter._format_value(value)
                    data.append(row_data)
                
                df = pd.DataFrame(data)
                
                # Başlıkları uygula
                headers = self.exporter.get_field_headers()
                df = df.rename(columns=headers)
                
                yield df
        
        # Chunk'ları yaz
        writer = MemoryEfficientExcelWriter(output)
        writer.write_chunks(chunk_generator(), **options)
        
        output.seek(0)
        return output.getvalue()
    
    def get_import_statistics(self, results: Dict[str, Any]) -> str:
        """Import sonuçlarının özet istatistiklerini oluştur"""
        success_rate = (results['success_count'] / results['total_rows'] * 100) if results['total_rows'] > 0 else 0
        
        return f"""
        Import İstatistikleri:
        - Toplam Satır: {results['total_rows']}
        - Başarılı: {results['success_count']}
        - Hatalı: {results['error_count']}
        - Uyarı: {results['warning_count']}
        - Başarı Oranı: {success_rate:.1f}%
        """