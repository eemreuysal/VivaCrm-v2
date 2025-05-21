"""
Progress tracking for Excel import operations.
"""
from django.core.cache import cache
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


class ImportProgress:
    """
    Progress tracker for Excel imports with real-time updates.
    """
    
    def __init__(self, session_id, total_rows=0, use_websocket=True):
        self.session_id = session_id
        self.total_rows = total_rows
        self.processed = 0
        self.errors = []
        self.warnings = []
        self.start_time = timezone.now()
        self.use_websocket = use_websocket
        self.cache_key = f"import_progress_{session_id}"
        
        # Initialize progress data
        self.progress_data = {
            'session_id': session_id,
            'total': total_rows,
            'processed': 0,
            'errors': 0,
            'warnings': 0,
            'status': 'initializing',
            'start_time': self.start_time.isoformat(),
            'progress_percentage': 0
        }
        self._update_cache()
    
    def update(self, row_num, success=True, error=None, warning=None):
        """
        Update progress for a specific row.
        
        Args:
            row_num: Current row number being processed
            success: Whether the row was processed successfully
            error: Error message if processing failed
            warning: Warning message if there were non-critical issues
        """
        self.processed = row_num
        
        if error:
            self.errors.append({'row': row_num, 'error': error})
            self.progress_data['errors'] = len(self.errors)
        
        if warning:
            self.warnings.append({'row': row_num, 'warning': warning})
            self.progress_data['warnings'] = len(self.warnings)
        
        # Update progress data
        self.progress_data.update({
            'processed': self.processed,
            'status': 'processing',
            'progress_percentage': (self.processed / self.total_rows * 100) if self.total_rows > 0 else 0,
            'last_update': timezone.now().isoformat()
        })
        
        # Save to cache
        self._update_cache()
        
        # Send WebSocket update
        if self.use_websocket:
            self._send_websocket_update()
    
    def complete(self, success_count=0):
        """
        Mark the import as complete.
        
        Args:
            success_count: Number of successfully imported rows
        """
        end_time = timezone.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.progress_data.update({
            'status': 'completed',
            'success_count': success_count,
            'end_time': end_time.isoformat(),
            'duration': duration,
            'progress_percentage': 100
        })
        
        self._update_cache()
        
        if self.use_websocket:
            self._send_websocket_update()
    
    def fail(self, error_message):
        """
        Mark the import as failed.
        
        Args:
            error_message: Error message describing the failure
        """
        end_time = timezone.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.progress_data.update({
            'status': 'failed',
            'error_message': error_message,
            'end_time': end_time.isoformat(),
            'duration': duration
        })
        
        self._update_cache()
        
        if self.use_websocket:
            self._send_websocket_update()
    
    def _update_cache(self):
        """
        Update the cache with current progress data.
        """
        cache.set(self.cache_key, self.progress_data, timeout=3600)  # 1 hour timeout
    
    def _send_websocket_update(self):
        """
        Send progress update via WebSocket.
        """
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'import_progress_{self.session_id}',
                {
                    'type': 'import_progress',
                    'message': self.progress_data
                }
            )
        except Exception as e:
            # Log error but don't fail the import
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send WebSocket update: {str(e)}")
    
    def get_progress(self):
        """
        Get current progress data.
        
        Returns:
            Dict containing current progress information
        """
        return self.progress_data
    
    @classmethod
    def get_cached_progress(cls, session_id):
        """
        Get progress data from cache.
        
        Args:
            session_id: Import session ID
            
        Returns:
            Dict containing progress data or None if not found
        """
        cache_key = f"import_progress_{session_id}"
        return cache.get(cache_key)