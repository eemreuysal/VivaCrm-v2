from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import os
import shutil
import subprocess
import json
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


@shared_task
def backup_database():
    """
    Create a backup of the database and save it to the backups directory.
    """
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'db')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"db_backup_{timestamp}.sqlite3"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # For SQLite, just copy the file
        shutil.copy2(settings.DATABASES['default']['NAME'], backup_path)
        
        # For PostgreSQL, you would use pg_dump:
        # subprocess.run([
        #     'pg_dump',
        #     '-U', settings.DATABASES['default']['USER'],
        #     '-d', settings.DATABASES['default']['NAME'],
        #     '-f', backup_path
        # ], check=True)
        
        # Log the successful backup
        backup_size = os.path.getsize(backup_path)
        logger.info(f"Database backup created: {backup_path} ({backup_size} bytes)")
        
        # Remove old backups (keep only last 10)
        all_backups = sorted(
            [os.path.join(backup_dir, f) for f in os.listdir(backup_dir)],
            key=os.path.getctime
        )
        if len(all_backups) > 10:
            for old_backup in all_backups[:-10]:
                os.remove(old_backup)
                logger.info(f"Removed old backup: {old_backup}")
        
        return f"Database backup created: {backup_path}"
    
    except Exception as e:
        error_msg = f"Database backup failed: {str(e)}"
        logger.error(error_msg)
        return error_msg


@shared_task
def backup_media_files():
    """
    Create a backup of the media files and save it to the backups directory.
    """
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'media')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"media_backup_{timestamp}.zip"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Create a zip archive of the media directory
        # Exclude the backups directory itself to avoid recursion
        media_dir = settings.MEDIA_ROOT
        exclude_backups = os.path.join(media_dir, 'backups')
        
        # Use shutil.make_archive or subprocess.run with zip command
        shutil.make_archive(
            backup_path[:-4],  # Remove .zip extension for make_archive
            'zip',
            root_dir=media_dir,
            base_dir='.',
            logger=logger
        )
        
        # Log the successful backup
        backup_size = os.path.getsize(backup_path)
        logger.info(f"Media backup created: {backup_path} ({backup_size} bytes)")
        
        # Remove old backups (keep only last 5)
        all_backups = sorted(
            [os.path.join(backup_dir, f) for f in os.listdir(backup_dir)],
            key=os.path.getctime
        )
        if len(all_backups) > 5:
            for old_backup in all_backups[:-5]:
                os.remove(old_backup)
                logger.info(f"Removed old backup: {old_backup}")
        
        return f"Media files backup created: {backup_path}"
    
    except Exception as e:
        error_msg = f"Media backup failed: {str(e)}"
        logger.error(error_msg)
        return error_msg


@shared_task
def clean_old_files():
    """
    Clean old temporary files and logs.
    """
    # Define directories to clean and how old files should be to delete
    cleanup_dirs = [
        # (directory, days_old)
        (os.path.join(settings.MEDIA_ROOT, 'reports'), 90),
        (os.path.join(settings.MEDIA_ROOT, 'cache'), 7),
        (os.path.join(settings.BASE_DIR, 'logs'), 30),
    ]
    
    deleted_count = 0
    deleted_size = 0
    cutoff_date = timezone.now() - timedelta(days=365)  # Maximum age for any file
    
    for directory, days_old in cleanup_dirs:
        if not os.path.exists(directory):
            continue
        
        # Calculate the cutoff date for this directory
        dir_cutoff = timezone.now() - timedelta(days=days_old)
        
        # Use the more restrictive of the two cutoffs
        if dir_cutoff < cutoff_date:
            dir_cutoff = cutoff_date
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_time = os.path.getmtime(file_path)
                    file_date = timezone.datetime.fromtimestamp(file_time, tz=timezone.utc)
                    
                    if file_date < dir_cutoff:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        deleted_size += file_size
                        logger.info(f"Deleted old file: {file_path} ({file_size} bytes)")
                except Exception as e:
                    logger.error(f"Error cleaning file {file_path}: {str(e)}")
    
    return f"Cleaned {deleted_count} old files, freeing {deleted_size / (1024 * 1024):.2f} MB"


@shared_task
def notify_admins_of_system_errors():
    """
    Check error logs and notify administrators of any recent errors.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Define the log file to check
    log_file = os.path.join(settings.BASE_DIR, 'logs', 'error.log')
    if not os.path.exists(log_file):
        return "No error log found"
    
    # Check how recently the file was modified
    file_time = os.path.getmtime(log_file)
    file_date = timezone.datetime.fromtimestamp(file_time, tz=timezone.utc)
    
    # Only process if errors occurred in the last 24 hours
    if file_date < timezone.now() - timedelta(hours=24):
        return "No recent errors found"
    
    # Read the last 100 lines from the error log
    try:
        with open(log_file, 'r') as f:
            # Get the last 100 lines
            lines = f.readlines()[-100:]
            
            # Count ERROR and CRITICAL lines
            error_count = sum(1 for line in lines if "ERROR" in line or "CRITICAL" in line)
            
            if error_count > 0:
                # Get admin emails
                admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
                
                # Send notification
                error_sample = "\n".join(line for line in lines[-10:] if "ERROR" in line or "CRITICAL" in line)
                
                send_mail(
                    subject=f"VivaCRM System Alert: {error_count} errors detected",
                    message=f"""
                    Dear Administrator,
                    
                    {error_count} errors were detected in the VivaCRM system logs in the last 24 hours.
                    
                    Here is a sample of the recent errors:
                    
                    {error_sample}
                    
                    Please check the full logs at {log_file} for more details.
                    
                    This is an automated message from the VivaCRM System.
                    """,
                    from_email=settings.SERVER_EMAIL,
                    recipient_list=list(admin_emails),
                    fail_silently=False,
                )
                
                return f"Notified administrators about {error_count} recent errors"
            
            return "No errors found in recent log entries"
            
    except Exception as e:
        logger.error(f"Error processing error logs: {str(e)}")
        return f"Error checking log file: {str(e)}"