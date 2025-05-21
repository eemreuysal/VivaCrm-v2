"""
Memory management utilities for Excel operations.
"""
import gc
import psutil
import os
from django.core.cache import cache
from django.conf import settings
import logging
from functools import wraps
import tempfile
import shutil
import pandas as pd
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages memory usage during Excel operations.
    """
    
    def __init__(self, max_memory_mb=500):
        self.max_memory_mb = max_memory_mb
        self.initial_memory = None
        self.temp_files = []
    
    def check_memory_usage(self):
        """
        Check current memory usage.
        
        Returns:
            Dictionary with memory statistics
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available / 1024 / 1024  # MB
        }
    
    def enforce_memory_limit(self):
        """
        Check if memory usage exceeds limit and take action.
        
        Raises:
            MemoryError: If memory usage is too high
        """
        current_memory = self.check_memory_usage()
        
        if current_memory['rss'] > self.max_memory_mb:
            # Try to free memory
            self.cleanup()
            gc.collect()
            
            # Check again
            current_memory = self.check_memory_usage()
            if current_memory['rss'] > self.max_memory_mb:
                raise MemoryError(
                    f"Memory usage ({current_memory['rss']:.1f}MB) exceeds "
                    f"limit ({self.max_memory_mb}MB)"
                )
    
    def cleanup(self):
        """
        Clean up temporary resources.
        """
        # Clear cache entries
        self._clear_expired_cache()
        
        # Remove temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.error(f"Error removing temp file {temp_file}: {str(e)}")
        
        self.temp_files.clear()
        
        # Force garbage collection
        gc.collect()
    
    def _clear_expired_cache(self):
        """
        Clear expired cache entries related to Excel imports.
        """
        cache_keys = [
            'excel_import_*',
            'import_progress_*',
            'correction_data_*'
        ]
        
        for pattern in cache_keys:
            # Django cache doesn't support pattern deletion,
            # so we need to track keys separately
            keys_to_delete = self._get_cache_keys_by_pattern(pattern)
            for key in keys_to_delete:
                cache.delete(key)
                logger.debug(f"Deleted cache key: {key}")
    
    def _get_cache_keys_by_pattern(self, pattern):
        """
        Get cache keys matching a pattern.
        Note: This is a simplified implementation.
        """
        # In production, you might want to use Redis SCAN command
        # or maintain a separate index of cache keys
        return []
    
    def create_temp_file(self, suffix='.xlsx'):
        """
        Create a temporary file and track it for cleanup.
        
        Returns:
            Path to temporary file
        """
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(temp_fd)
        self.temp_files.append(temp_path)
        return temp_path
    
    def __enter__(self):
        """Context manager entry."""
        self.initial_memory = self.check_memory_usage()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        
        # Log memory usage delta
        if self.initial_memory:
            final_memory = self.check_memory_usage()
            delta = final_memory['rss'] - self.initial_memory['rss']
            logger.info(f"Memory delta: {delta:.1f}MB")


def cleanup_import_session(session_id):
    """
    Clean up import session data.
    
    Args:
        session_id: Import session ID
    """
    cache_keys = [
        f"excel_import_{session_id}",
        f"import_progress_{session_id}",
        f"correction_data_{session_id}"
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    # Remove temporary files
    temp_dir = getattr(settings, 'EXCEL_TEMP_DIR', '/tmp/excel_imports')
    session_dir = os.path.join(temp_dir, session_id)
    
    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
            logger.info(f"Removed session directory: {session_dir}")
        except Exception as e:
            logger.error(f"Error removing session directory: {str(e)}")
    
    # Force garbage collection
    gc.collect()


def memory_efficient(max_memory_mb=500):
    """
    Decorator to ensure memory-efficient execution.
    
    Args:
        max_memory_mb: Maximum allowed memory usage in MB
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with MemoryManager(max_memory_mb) as memory_manager:
                # Check memory before execution
                memory_manager.enforce_memory_limit()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Check memory after execution
                    memory_manager.enforce_memory_limit()
                    
                    return result
                finally:
                    # Always cleanup
                    memory_manager.cleanup()
        
        return wrapper
    return decorator


class ChunkedDataProcessor:
    """
    Process large datasets in chunks to avoid memory issues.
    """
    
    def __init__(self, chunk_size=1000):
        self.chunk_size = chunk_size
    
    def process_dataframe(self, df, processor_func):
        """
        Process a pandas DataFrame in chunks.
        
        Args:
            df: Pandas DataFrame
            processor_func: Function to process each chunk
            
        Returns:
            Combined results from all chunks
        """
        results = []
        total_rows = len(df)
        
        for start_idx in range(0, total_rows, self.chunk_size):
            end_idx = min(start_idx + self.chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx]
            
            # Process chunk
            chunk_result = processor_func(chunk)
            results.append(chunk_result)
            
            # Free memory
            del chunk
            gc.collect()
            
            logger.debug(f"Processed rows {start_idx}-{end_idx} of {total_rows}")
        
        return results
    
    def read_excel_chunked(self, file_path, sheet_name=0):
        """
        Read Excel file in chunks.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name or index
            
        Yields:
            DataFrame chunks
        """
        import pandas as pd
        
        # Get total rows first
        df_sample = pd.read_excel(file_path, sheet_name=sheet_name, nrows=1)
        
        # Read in chunks
        for chunk in pd.read_excel(
            file_path, 
            sheet_name=sheet_name, 
            chunksize=self.chunk_size
        ):
            yield chunk
            
            # Free memory after each chunk
            gc.collect()