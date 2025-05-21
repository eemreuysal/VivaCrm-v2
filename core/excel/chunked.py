"""
Büyük Excel dosyaları için chunk-based okuma işlemleri.
Memory-efficient Excel processing.
"""
from typing import Iterator, Dict, Any, Optional, Union
import pandas as pd
from pathlib import Path
import logging
from .exceptions import FileSizeError, UnsupportedFileTypeError

logger = logging.getLogger(__name__)


class ChunkedExcelReader:
    """
    Büyük Excel dosyalarını memory-efficient şekilde okumak için.
    Iterator pattern kullanarak dosyayı parça parça işler.
    """
    
    # Desteklenen dosya uzantıları
    SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.xlsm', '.xlsb'}
    
    # Varsayılan ayarlar
    DEFAULT_CHUNK_SIZE = 1000
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(
        self,
        file_path: Union[str, Path],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_file_size: int = MAX_FILE_SIZE
    ):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.max_file_size = max_file_size
        self._validate_file()
        
    def _validate_file(self):
        """Dosya validasyonu"""
        # Dosya var mı?
        if not self.file_path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {self.file_path}")
        
        # Uzantı kontrol
        if self.file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Desteklenmeyen dosya tipi: {self.file_path.suffix}",
                file_type=self.file_path.suffix,
                supported_types=list(self.SUPPORTED_EXTENSIONS)
            )
        
        # Boyut kontrol
        file_size = self.file_path.stat().st_size
        if file_size > self.max_file_size:
            raise FileSizeError(
                f"Dosya boyutu çok büyük: {file_size / (1024*1024):.2f}MB",
                max_size=self.max_file_size,
                actual_size=file_size
            )
    
    def read_chunks(
        self,
        sheet_name: Union[str, int] = 0,
        skiprows: int = 0,
        usecols: Optional[list] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Excel dosyasını chunk'lar halinde oku.
        Generator pattern kullanarak memory kullanımını optimize eder.
        """
        try:
            # Excel dosyasını aç
            excel_file = pd.ExcelFile(self.file_path, engine='openpyxl')
            
            # Sheet kontrolü
            if isinstance(sheet_name, str) and sheet_name not in excel_file.sheet_names:
                raise ValueError(f"Sheet bulunamadı: {sheet_name}")
            
            # İlk satırları oku (header'ları almak için)
            df_header = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name,
                nrows=0,
                skiprows=skiprows,
                usecols=usecols
            )
            
            total_rows = self._get_total_rows(excel_file, sheet_name, skiprows)
            processed_rows = 0
            
            while processed_rows < total_rows:
                # Chunk oku
                df_chunk = pd.read_excel(
                    self.file_path,
                    sheet_name=sheet_name,
                    skiprows=skiprows + processed_rows + 1,  # +1 for header
                    nrows=self.chunk_size,
                    names=df_header.columns.tolist(),
                    usecols=usecols
                )
                
                if df_chunk.empty:
                    break
                
                yield df_chunk
                
                processed_rows += len(df_chunk)
                
                logger.debug(
                    f"İşlenen satır: {processed_rows}/{total_rows} "
                    f"({processed_rows/total_rows*100:.1f}%)"
                )
                
        except Exception as e:
            logger.error(f"Excel okuma hatası: {str(e)}")
            raise
    
    def _get_total_rows(
        self,
        excel_file: pd.ExcelFile,
        sheet_name: Union[str, int],
        skiprows: int = 0
    ) -> int:
        """Toplam satır sayısını hesapla"""
        # Tüm dosyayı okumadan satır sayısını tahmin et
        # Küçük bir örnek oku
        sample_df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            skiprows=skiprows,
            nrows=1000
        )
        
        # Eğer örnek 1000 satırdan azsa, toplam satır sayısı bellidir
        if len(sample_df) < 1000:
            return len(sample_df)
        
        # Büyük dosyalar için tahmini satır sayısı
        # (Dosya boyutuna göre tahmin yapılabilir)
        file_size = self.file_path.stat().st_size
        avg_row_size = file_size / 1000  # Örnek üzerinden tahmin
        estimated_rows = int(file_size / avg_row_size)
        
        return estimated_rows
    
    def process_file(
        self,
        processor_func,
        sheet_name: Union[str, int] = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Dosyayı chunk'lar halinde işle.
        
        Args:
            processor_func: Her chunk için çağrılacak fonksiyon
            sheet_name: Okunacak sheet
            **kwargs: read_chunks'a geçilecek parametreler
            
        Returns:
            İşlem sonuçları
        """
        results = {
            'total_chunks': 0,
            'total_rows': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            for chunk_index, df_chunk in enumerate(self.read_chunks(sheet_name, **kwargs)):
                try:
                    # Chunk'ı işle
                    chunk_result = processor_func(df_chunk, chunk_index)
                    
                    # Sonuçları birleştir
                    results['total_chunks'] += 1
                    results['total_rows'] += len(df_chunk)
                    
                    if 'errors' in chunk_result:
                        results['errors'].extend(chunk_result['errors'])
                    
                    if 'warnings' in chunk_result:
                        results['warnings'].extend(chunk_result['warnings'])
                        
                except Exception as e:
                    results['errors'].append({
                        'chunk': chunk_index,
                        'error': str(e),
                        'type': type(e).__name__
                    })
                    logger.error(f"Chunk {chunk_index} işleme hatası: {str(e)}")
        
        except Exception as e:
            results['errors'].append({
                'error': str(e),
                'type': type(e).__name__
            })
            logger.error(f"Dosya işleme hatası: {str(e)}")
        
        return results


class MemoryEfficientExcelWriter:
    """
    Büyük Excel dosyaları yazmak için memory-efficient writer.
    Streaming mode kullanarak büyük veri setlerini yazar.
    """
    
    def __init__(self, output_path: Union[str, Path]):
        self.output_path = Path(output_path)
        self._ensure_directory()
        
    def _ensure_directory(self):
        """Dizin varsa oluştur"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def write_chunks(
        self,
        data_iterator: Iterator[pd.DataFrame],
        sheet_name: str = 'Sheet1',
        **kwargs
    ):
        """
        Veriyi chunk'lar halinde Excel'e yaz.
        Constant memory mode kullanarak büyük veri setlerini yazar.
        """
        with pd.ExcelWriter(
            self.output_path,
            engine='openpyxl',
            mode='w'
        ) as writer:
            
            # İlk chunk'ı al ve header'ları yaz
            first_chunk = next(data_iterator, None)
            if first_chunk is None:
                return
            
            startrow = 0
            first_chunk.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
                startrow=startrow
            )
            startrow += len(first_chunk) + 1  # +1 for header
            
            # Geri kalan chunk'ları yaz
            for chunk in data_iterator:
                chunk.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                    header=False,
                    startrow=startrow
                )
                startrow += len(chunk)
                
                logger.debug(f"Yazılan satır: {startrow}")
        
        logger.info(f"Excel dosyası oluşturuldu: {self.output_path}")