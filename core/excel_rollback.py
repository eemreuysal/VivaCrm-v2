"""
Rollback mechanism for Excel import operations.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)


class TransactionalImporter:
    """
    Provides transactional import with rollback capability.
    """
    
    def __init__(self, importer, backup_service=None):
        self.importer = importer
        self.backup_service = backup_service
        self.created_objects = []
        self.updated_objects = []
        self.import_metadata = {
            'start_time': None,
            'end_time': None,
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'rollback_info': None
        }
    
    def import_with_rollback(self, file_obj, **kwargs):
        """
        Import data with automatic rollback on failure.
        
        Args:
            file_obj: Excel file to import
            **kwargs: Additional arguments for the importer
            
        Returns:
            Import result with rollback information if applicable
        """
        self.import_metadata['start_time'] = timezone.now()
        backup_file = None
        
        try:
            # Create backup before import
            if self.backup_service:
                backup_file = self.backup_service.create_backup(
                    self.importer.model,
                    description=f"Pre-import backup {timezone.now()}"
                )
            
            # Start transaction
            with transaction.atomic():
                # Use savepoint for nested transactions
                savepoint = transaction.savepoint()
                
                try:
                    # Perform the import
                    result = self.importer.import_data(file_obj, **kwargs)
                    
                    # Store created/updated objects for potential rollback
                    self.created_objects = result.get('created_objects', [])
                    self.updated_objects = result.get('updated_objects', [])
                    
                    # Validate the import results
                    self._validate_import_results(result)
                    
                    # If validation passes, commit the savepoint
                    transaction.savepoint_commit(savepoint)
                    
                    self.import_metadata.update({
                        'end_time': timezone.now(),
                        'total_processed': result.get('total', 0),
                        'success_count': result.get('success', 0),
                        'error_count': result.get('errors', 0)
                    })
                    
                    return {
                        'success': True,
                        'result': result,
                        'metadata': self.import_metadata,
                        'backup_file': backup_file
                    }
                    
                except Exception as e:
                    # Rollback to savepoint
                    transaction.savepoint_rollback(savepoint)
                    
                    # Log rollback information
                    self.import_metadata['rollback_info'] = {
                        'reason': str(e),
                        'created_count': len(self.created_objects),
                        'updated_count': len(self.updated_objects),
                        'timestamp': timezone.now().isoformat()
                    }
                    
                    logger.error(f"Import failed, rolling back: {str(e)}")
                    raise
                    
        except Exception as e:
            self.import_metadata['end_time'] = timezone.now()
            self.import_metadata['error'] = str(e)
            
            # If we have a backup, provide restore instructions
            restore_info = None
            if backup_file:
                restore_info = {
                    'backup_file': backup_file,
                    'restore_command': f"python manage.py restore_backup {backup_file}",
                    'message': "Import gagal. Gunakan perintah di atas untuk mengembalikan data."
                }
            
            return {
                'success': False,
                'error': str(e),
                'metadata': self.import_metadata,
                'restore_info': restore_info
            }
    
    def _validate_import_results(self, result):
        """
        Validate import results and raise exception if validation fails.
        
        Args:
            result: Import result dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for critical errors
        critical_errors = result.get('critical_errors', [])
        if critical_errors:
            raise ValidationError(f"Critical errors found: {critical_errors}")
        
        # Check error threshold (fail if more than 10% errors)
        total = result.get('total', 0)
        errors = result.get('errors', 0)
        
        if total > 0:
            error_percentage = (errors / total) * 100
            if error_percentage > 10:
                raise ValidationError(
                    f"Too many errors: {errors}/{total} ({error_percentage:.1f}%)"
                )
        
        # Custom validation logic can be added here
        self._custom_validation(result)
    
    def _custom_validation(self, result):
        """
        Custom validation logic for specific business rules.
        Override this method in subclasses for custom validation.
        
        Args:
            result: Import result dictionary
        """
        pass


class BackupService:
    """
    Service for creating and managing backups.
    """
    
    def __init__(self, backup_dir='/tmp/excel_backups'):
        self.backup_dir = backup_dir
        
        # Create backup directory if it doesn't exist
        import os
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, model, description=""):
        """
        Create a backup of model data.
        
        Args:
            model: Django model class
            description: Backup description
            
        Returns:
            Path to backup file
        """
        from django.core import serializers
        import os
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{model._meta.label}_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, filename)
        
        # Serialize model data
        data = serializers.serialize('json', model.objects.all())
        
        # Create backup metadata
        metadata = {
            'model': model._meta.label,
            'timestamp': timezone.now().isoformat(),
            'description': description,
            'record_count': model.objects.count()
        }
        
        # Save backup with metadata
        backup_data = {
            'metadata': metadata,
            'data': json.loads(data)
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    
    def restore_backup(self, backup_path):
        """
        Restore data from a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Restore result information
        """
        from django.core import serializers
        from django.apps import apps
        
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        metadata = backup_data['metadata']
        model_label = metadata['model']
        
        # Get model class
        app_label, model_name = model_label.split('.')
        model = apps.get_model(app_label, model_name)
        
        # Clear existing data
        model.objects.all().delete()
        
        # Restore data
        data_json = json.dumps(backup_data['data'])
        objects = serializers.deserialize('json', data_json)
        
        restored_count = 0
        for obj in objects:
            obj.save()
            restored_count += 1
        
        logger.info(f"Restored {restored_count} records from {backup_path}")
        
        return {
            'success': True,
            'restored_count': restored_count,
            'model': model_label,
            'backup_timestamp': metadata['timestamp']
        }