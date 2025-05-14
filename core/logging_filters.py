"""
Logging filters for tracking requests and adding metadata to logs.
"""
import logging
import uuid
import threading

# Thread-local storage to save trace ID per request
_thread_local = threading.local()


def get_current_trace_id():
    """
    Get the current trace ID for this request/thread.
    If no trace ID exists, create a new one.
    
    Returns:
        str: The trace ID
    """
    if not hasattr(_thread_local, 'trace_id'):
        _thread_local.trace_id = str(uuid.uuid4())
    return _thread_local.trace_id


def set_current_trace_id(trace_id=None):
    """
    Set the current trace ID for this request/thread.
    If trace_id is None, a new ID is generated.
    
    Args:
        trace_id: Optional trace ID to set
    """
    _thread_local.trace_id = trace_id or str(uuid.uuid4())


def clear_current_trace_id():
    """
    Clear the current trace ID from thread-local storage.
    """
    if hasattr(_thread_local, 'trace_id'):
        del _thread_local.trace_id


class TraceIdFilter(logging.Filter):
    """
    Logging filter that adds a trace ID to log records.
    The trace ID is a UUID that is unique to each request/thread.
    """
    
    def filter(self, record):
        """
        Add trace_id attribute to the log record if it's not already present.
        
        Args:
            record: The log record to modify
            
        Returns:
            bool: Always True (to include the record in the log)
        """
        if not hasattr(record, 'trace_id'):
            record.trace_id = get_current_trace_id()
        return True


class TraceIdMiddleware:
    """
    Middleware that assigns a trace ID to each request.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Generate new trace ID for this request
        set_current_trace_id()
        
        # Add trace ID to request for easy access
        request.trace_id = get_current_trace_id()
        
        # Add trace ID to response headers
        response = self.get_response(request)
        response['X-Trace-ID'] = get_current_trace_id()
        
        # Clean up trace ID after request is complete
        clear_current_trace_id()
        
        return response