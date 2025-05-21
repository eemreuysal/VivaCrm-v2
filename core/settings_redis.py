# Redis Cache Yapılandırması
import os
from django.core.cache import cache

# Redis Cache Settings
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = int(os.environ.get('REDIS_DB', '0'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
REDIS_SSL = os.environ.get('REDIS_SSL', 'False').lower() == 'true'

# Cache configuration for production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{":" + REDIS_PASSWORD + "@" if REDIS_PASSWORD else ""}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {}
            },
            'SSL_CERT_REQS': 'required' if REDIS_SSL else None,
        },
        'KEY_PREFIX': 'vivacrm',
        'VERSION': 1,
        'TIMEOUT': 300  # 5 dakika default timeout
    },
    # Session cache
    'session': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{":" + REDIS_PASSWORD + "@" if REDIS_PASSWORD else ""}{REDIS_HOST}:{REDIS_PORT}/1',
        'OPTIONS': {
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'vivacrm_session',
        'TIMEOUT': 86400  # 24 saat
    },
    # API response cache
    'api': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{":" + REDIS_PASSWORD + "@" if REDIS_PASSWORD else ""}{REDIS_HOST}:{REDIS_PORT}/2',
        'OPTIONS': {
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'vivacrm_api',
        'TIMEOUT': 600  # 10 dakika
    }
}

# Session backend with Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'
SESSION_COOKIE_AGE = 86400  # 24 saat

# Cache middleware configuration
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300  # 5 dakika
CACHE_MIDDLEWARE_KEY_PREFIX = 'vivacrm_page'

# Conditional caching settings
CACHE_CONTROL_MAX_AGE = 300  # 5 dakika
USE_ETAGS = True
CONDITIONAL_GET_ETAG = True