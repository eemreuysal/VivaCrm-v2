# Import celery app her zaman y�klensin
from .celery import app as celery_app

__all__ = ('celery_app',)