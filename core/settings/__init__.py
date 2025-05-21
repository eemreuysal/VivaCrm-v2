"""
Django settings module selector
"""
import os

# Ortam değişkenine göre ayar modülünü seç
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from .production import *
elif DJANGO_ENV == 'test':
    from .test import *
else:
    from .development import *