"""
Celery tasks for Excel import/export operations.
"""
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from .excel import ExcelImporter
from .models_import import ImportTask
import logging
import json

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_excel_import_async(self, file_path, model_name, import_config, user_id=None):
    """
    Async task for processing Excel imports.
    
    Args:
        file_path: Path to the uploaded Excel file
        model_name: Name of the model to import data into
        import_config: Configuration dictionary for the import
        user_id: ID of the user performing the import
    """
    task_id = self.request.id
    cache_key = f"import_progress_{task_id}"
    
    # Initialize progress tracking
    progress_data = {
        'status': 'in_progress',
        'total': 0,
        'processed': 0,
        'errors': 0,
        'success': 0,
        'start_time': timezone.now().isoformat()
    }
    cache.set(cache_key, progress_data, timeout=3600)
    
    try:
        # Get the model class
        from django.apps import apps
        model = apps.get_model(model_name)
        
        # Get user if provided
        user = None
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
        
        # Create importer instance
        importer = ExcelImporter(
            model=model,
            **import_config
        )
        
        # Process import
        result = importer.import_data(
            file_obj=file_path,
            user=user
        )
        
        # Update progress
        progress_data.update({
            'status': 'completed',
            'processed': result.total_processed,
            'errors': result.error_count,
            'success': result.success_count,
            'end_time': timezone.now().isoformat()
        })
        cache.set(cache_key, progress_data, timeout=3600)
        
        return {
            'success': True,
            'result': result.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Async import error: {str(e)}", exc_info=True)
        
        # Update progress with error
        progress_data.update({
            'status': 'failed',
            'error': str(e),
            'end_time': timezone.now().isoformat()
        })
        cache.set(cache_key, progress_data, timeout=3600)
        
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def check_import_progress(task_id):
    """
    Check the progress of an import task.
    """
    cache_key = f"import_progress_{task_id}"
    progress_data = cache.get(cache_key)
    
    if not progress_data:
        return {
            'status': 'not_found',
            'message': 'Task not found or expired'
        }
    
    return progress_data


@shared_task
def cleanup_expired_imports():
    """
    Clean up expired import sessions and files.
    """
    from django.conf import settings
    import os
    from datetime import timedelta
    
    # Clean up files older than 24 hours
    temp_dir = getattr(settings, 'EXCEL_TEMP_DIR', '/tmp/excel_imports')
    if os.path.exists(temp_dir):
        current_time = timezone.now()
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_time = timezone.datetime.fromtimestamp(os.path.getmtime(file_path))
                if current_time - file_time > timedelta(hours=24):
                    try:
                        os.remove(file_path)
                        logger.info(f"Cleaned up expired file: {filename}")
                    except Exception as e:
                        logger.error(f"Error cleaning up file {filename}: {str(e)}")