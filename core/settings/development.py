from .base import *
import os

# Development ayarları
DEBUG = True
ALLOWED_HOSTS = ['*']

# Güvenlik ayarlarını development için devre dışı bırak
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Redis Cache Konfigürasyonu (Development)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Development'ta hataları yoksay
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,  # Development için yeterli
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
            },
            # Parser belirtmeyelim, varsayılan kullanılsın
        },
        'KEY_PREFIX': 'vivacrm_dev',
        'VERSION': 1,
        'TIMEOUT': 300,  # 5 dakika
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
            # Parser belirtmeyelim, varsayılan kullanılsın
        },
        'KEY_PREFIX': 'vivacrm_dev_session',
        'TIMEOUT': 86400,  # 24 saat
    }
}

# Session backend
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 0  # Development'ta cache kapalı
CACHE_MIDDLEWARE_KEY_PREFIX = 'vivacrm_dev_page'

# Debug Toolbar - We'll just set the internal IPs since the app is already included in base.py
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1']

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'django_redis': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Redis debug için
        },
        'redis': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}
