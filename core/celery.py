"""
Celery configuration for VivaCRM v2.

This module configures Celery for asynchronous task processing in the application.
It sets up the Celery app instance, loads configuration from Django settings,
and provides infrastructure for handling background tasks throughout the application.
"""

import os
from celery import Celery

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create Celery application
app = Celery('vivacrm_v2')

# Load configuration from Django settings using a namespace
# This allows us to use settings prefixed with CELERY_ in Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load periodic task schedules from separate config module
app.config_from_object('core.celery_config')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Debug task that prints the task request information.
    
    This task is used for debugging Celery task execution.
    It prints the task request object to show details about the task execution.
    
    Args:
        self: Task instance (automatically passed by Celery)
    
    Returns:
        None
    """
    print(f'Request: {self.request!r}')