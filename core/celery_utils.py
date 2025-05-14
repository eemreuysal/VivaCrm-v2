"""
Utility functions for working with Celery tasks across the application.
"""
from functools import wraps
from celery.result import AsyncResult
from django.conf import settings
import logging
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


def get_task_status(task_id):
    """
    Get the status of a Celery task by its ID.
    
    Args:
        task_id (str): The task ID to check
        
    Returns:
        dict: A dictionary with status information
    """
    result = AsyncResult(task_id)
    
    response = {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
    }
    
    if result.ready():
        if result.successful():
            response['result'] = result.get()
        else:
            response['error'] = str(result.result)
    
    return response


def log_task_execution(log_to_file=False):
    """
    Decorator to log task execution details.
    
    Args:
        log_to_file (bool): Whether to also log to a separate file
        
    Returns:
        function: Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            task_name = func.__name__
            start_time = datetime.now()
            
            logger.info(f"Task {task_name} started at {start_time}")
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"Task {task_name} completed in {duration:.2f} seconds")
                
                if log_to_file:
                    _log_to_file(task_name, start_time, end_time, duration, args, kwargs, result)
                
                return result
            
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.error(f"Task {task_name} failed after {duration:.2f} seconds. Error: {str(e)}")
                
                if log_to_file:
                    _log_to_file(task_name, start_time, end_time, duration, args, kwargs, 
                                 error=str(e), traceback=True)
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator


def _log_to_file(task_name, start_time, end_time, duration, args, kwargs, result=None, error=None, traceback=False):
    """
    Log task execution details to a file.
    
    Args:
        task_name (str): Name of the task
        start_time (datetime): Task start time
        end_time (datetime): Task end time
        duration (float): Task duration in seconds
        args (tuple): Task positional arguments
        kwargs (dict): Task keyword arguments
        result (any): Task result (if successful)
        error (str): Error message (if failed)
        traceback (bool): Whether to include traceback in log
    """
    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(settings.BASE_DIR, 'logs', 'tasks')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log filename based on date
        log_date = start_time.strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'{log_date}.log')
        
        # Prepare log entry
        log_entry = {
            'task': task_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'args': str(args),
            'kwargs': str(kwargs),
        }
        
        if result is not None:
            log_entry['result'] = str(result)
        
        if error is not None:
            log_entry['error'] = error
            
            if traceback:
                import traceback as tb
                log_entry['traceback'] = tb.format_exc()
        
        # Write log entry to file
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    except Exception as e:
        logger.error(f"Error writing task log to file: {str(e)}")


def revoke_stale_tasks(task_pattern, max_age_hours=24):
    """
    Revoke stale tasks that have been running for too long.
    
    Args:
        task_pattern (str): Pattern to match task names (e.g., 'app.tasks.*')
        max_age_hours (int): Maximum age in hours for a task to be considered stale
        
    Returns:
        int: Number of tasks revoked
    """
    from celery.app import app_or_default
    app = app_or_default()
    
    i = app.control.inspect()
    active_tasks = i.active() or {}
    
    revoke_count = 0
    max_age = timedelta(hours=max_age_hours)
    now = datetime.now()
    
    for worker_name, tasks in active_tasks.items():
        for task in tasks:
            task_name = task.get('name', '')
            task_id = task.get('id')
            
            if task_pattern in task_name:
                # Check task age
                started = datetime.fromtimestamp(task.get('time_start', 0))
                age = now - started
                
                if age > max_age:
                    # Revoke the task
                    app.control.revoke(task_id, terminate=True)
                    logger.warning(f"Revoked stale task {task_name} ({task_id}) running for {age}")
                    revoke_count += 1
    
    return revoke_count