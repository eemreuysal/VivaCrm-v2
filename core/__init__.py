# Import celery app her zaman yüklensin
from .celery import app as celery_app

__all__ = ('celery_app',)