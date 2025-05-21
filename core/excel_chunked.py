"""
Chunked Excel reading for memory efficiency.
"""
import gc
import pandas as pd
import psutil
import os
from typing import Iterator, Optional
import logging

logger = logging.getLogger(__name__)


class ChunkedExcelReader:
    """Read Excel files in chunks to minimize memory usage."""
    
    def __init__(self, file_path: str = None, file_buffer=None, chunk_size: int = 1000):
        self.file_path = file_path
        self.file_buffer = file_buffer
        self.chunk_size = chunk_size
        self._columns = None
        
    def read_chunks(self) -> Iterator[pd.DataFrame]:
        """Read Excel file in chunks."""
        try:
            # Try using pandas read_excel with chunksize
            if self.file_path:
                for chunk in pd.read_excel(self.file_path, chunksize=self.chunk_size):
                    yield chunk
            else:
                # For file buffer, read entire file and chunk manually
                df = pd.read_excel(self.file_buffer)
                total_rows = len(df)
                
                for start_idx in range(0, total_rows, self.chunk_size):
                    end_idx = min(start_idx + self.chunk_size, total_rows)
                    yield df.iloc[start_idx:end_idx]
                    
                # Clear the full dataframe from memory
                del df
                gc.collect()
                
        except Exception as e:
            logger.error(f"Error reading Excel in chunks: {str(e)}")
            # Fallback to manual chunking
            yield from self._manual_chunk_reading()
            
    def _manual_chunk_reading(self) -> Iterator[pd.DataFrame]:
        """Manual chunking approach for problematic files."""
        try:
            # Read file in smaller pieces
            start_row = 0
            
            while True:
                try:
                    if self.file_path:
                        chunk = pd.read_excel(
                            self.file_path,
                            skiprows=start_row if start_row > 0 else None,
                            nrows=self.chunk_size,
                            header=0 if start_row == 0 else None
                        )
                    else:
                        # Reset buffer position
                        self.file_buffer.seek(0)
                        
                        # Skip rows and read chunk
                        chunk = pd.read_excel(
                            self.file_buffer,
                            skiprows=start_row if start_row > 0 else None,
                            nrows=self.chunk_size,
                            header=0 if start_row == 0 else None
                        )
                    
                    if chunk.empty or len(chunk) == 0:
                        break
                        
                    # Store column names from first chunk
                    if start_row == 0:
                        self._columns = chunk.columns
                    elif self._columns is not None:
                        chunk.columns = self._columns
                        
                    yield chunk
                    start_row += self.chunk_size
                    
                    # Clear memory after each chunk
                    gc.collect()
                    
                except pd.errors.EmptyDataError:
                    break
                except Exception as e:
                    if start_row == 0:
                        raise e
                    break
                    
        except Exception as e:
            logger.error(f"Error in manual chunk reading: {str(e)}")
            raise


class MemoryEfficientFileHandler:
    """Handle large Excel files efficiently with memory management."""
    
    @staticmethod
    def get_memory_usage() -> float:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
        
    @staticmethod
    def log_memory(action: str):
        """Log memory usage."""
        memory_mb = MemoryEfficientFileHandler.get_memory_usage()
        logger.info(f"[Memory] {action}: {memory_mb:.1f}MB")
        
    @staticmethod
    def clear_memory():
        """Clear memory and run garbage collection."""
        gc.collect()
        
    @staticmethod
    def check_file_size(file_path: str = None, file_buffer=None) -> int:
        """Check file size in bytes."""
        if file_path:
            return os.path.getsize(file_path)
        elif file_buffer:
            file_buffer.seek(0, 2)
            size = file_buffer.tell()
            file_buffer.seek(0)
            return size
        return 0
        
    @staticmethod
    def should_use_chunks(file_size: int, memory_limit_mb: int = 100) -> bool:
        """Determine if file should be processed in chunks."""
        # Use chunks if file is larger than 5MB or memory is constrained
        return file_size > 5 * 1024 * 1024 or MemoryEfficientFileHandler.get_memory_usage() > memory_limit_mb


def process_excel_file(file_path: str = None, file_buffer=None, processor_func=None, chunk_size: int = 1000):
    """
    Process Excel file with automatic memory management.
    
    Args:
        file_path: Path to Excel file
        file_buffer: File buffer for uploaded files
        processor_func: Function to process each chunk
        chunk_size: Number of rows per chunk
        
    Returns:
        Processing results
    """
    handler = MemoryEfficientFileHandler()
    
    # Log initial memory
    handler.log_memory("Start")
    
    # Check file size
    file_size = handler.check_file_size(file_path, file_buffer)
    use_chunks = handler.should_use_chunks(file_size)
    
    if use_chunks:
        logger.info(f"Processing file in chunks (size: {file_size / 1024 / 1024:.1f}MB)")
        reader = ChunkedExcelReader(file_path, file_buffer, chunk_size)
        
        results = []
        for chunk_num, chunk in enumerate(reader.read_chunks()):
            logger.info(f"Processing chunk {chunk_num + 1}")
            
            if processor_func:
                result = processor_func(chunk)
                results.append(result)
                
            # Clear memory after each chunk
            handler.clear_memory()
            handler.log_memory(f"After chunk {chunk_num + 1}")
            
        return results
    else:
        logger.info("Processing file in memory")
        # Read entire file for small files
        df = pd.read_excel(file_path or file_buffer)
        
        if processor_func:
            result = processor_func(df)
        else:
            result = df
            
        handler.log_memory("End")
        return result