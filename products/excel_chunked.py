"""
Chunked Excel reader for large files with memory management
"""
import pandas as pd
import logging
from typing import Iterator, Optional
import gc

logger = logging.getLogger(__name__)


class ChunkedExcelReader:
    """Read Excel files in chunks to manage memory efficiently"""
    
    def __init__(self, file_path_or_buffer, chunk_size: int = 1000):
        self.file_path_or_buffer = file_path_or_buffer
        self.chunk_size = chunk_size
        self.total_rows = None
        
    def get_total_rows(self) -> Optional[int]:
        """Get total number of rows in Excel file"""
        try:
            # Read only the first column to count rows
            df = pd.read_excel(
                self.file_path_or_buffer, 
                usecols=[0],
                engine='openpyxl'
            )
            self.total_rows = len(df)
            del df  # Free memory
            gc.collect()
            return self.total_rows
        except Exception as e:
            logger.error(f"Error counting rows: {str(e)}")
            return None
    
    def read_chunks(self) -> Iterator[pd.DataFrame]:
        """Read Excel file in chunks"""
        try:
            # Reset file position if it's a file object
            if hasattr(self.file_path_or_buffer, 'seek'):
                self.file_path_or_buffer.seek(0)
            
            # Read in chunks
            start_row = 0
            
            while True:
                try:
                    # Read a chunk
                    chunk = pd.read_excel(
                        self.file_path_or_buffer,
                        engine='openpyxl',
                        skiprows=start_row,
                        nrows=self.chunk_size
                    )
                    
                    # If chunk is empty, we're done
                    if chunk.empty:
                        break
                    
                    # If this is not the first chunk, we need to handle headers
                    if start_row > 0:
                        # Get headers from first row
                        headers = pd.read_excel(
                            self.file_path_or_buffer,
                            engine='openpyxl',
                            nrows=1
                        )
                        chunk.columns = headers.columns
                    
                    yield chunk
                    
                    # Update start row for next chunk
                    start_row += self.chunk_size
                    
                    # Garbage collection after each chunk
                    gc.collect()
                    
                except Exception as e:
                    logger.error(f"Error reading chunk at row {start_row}: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in chunked reading: {str(e)}")
            raise
    
    def process_in_chunks(self, processor_func, **kwargs):
        """Process Excel file in chunks with a processor function"""
        total_processed = 0
        
        try:
            for chunk_num, chunk in enumerate(self.read_chunks()):
                logger.info(f"Processing chunk {chunk_num + 1}, rows {total_processed} to {total_processed + len(chunk)}")
                
                # Process chunk
                result = processor_func(chunk, **kwargs)
                
                # Update count
                total_processed += len(chunk)
                
                # Memory cleanup
                del chunk
                gc.collect()
                
            return total_processed
            
        except Exception as e:
            logger.error(f"Error processing chunks: {str(e)}")
            raise


def process_large_excel_file(file_obj, chunk_size: int = 500):
    """
    Process large Excel file with memory management
    
    Args:
        file_obj: File object or path
        chunk_size: Number of rows to process at once
        
    Returns:
        Generator yielding processed chunks
    """
    reader = ChunkedExcelReader(file_obj, chunk_size=chunk_size)
    
    # Get total rows for progress tracking
    total_rows = reader.get_total_rows()
    logger.info(f"Total rows to process: {total_rows}")
    
    # Process chunks
    for chunk in reader.read_chunks():
        yield chunk