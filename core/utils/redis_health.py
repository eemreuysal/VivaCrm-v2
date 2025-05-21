"""
Redis Health Check Utility
Redis bağlantısını kontrol etmek için kullanılır
"""
from django.core.cache import cache
from django_redis import get_redis_connection
import logging

logger = logging.getLogger(__name__)


def check_redis_connection():
    """
    Redis bağlantısını kontrol et
    
    Returns:
        bool: Bağlantı başarılı ise True, değilse False
    """
    try:
        # Basit bir set/get testi
        cache.set('health_check', 'ok', 1)
        result = cache.get('health_check')
        return result == 'ok'
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


def get_redis_info():
    """
    Redis sunucu bilgilerini al
    
    Returns:
        dict: Redis sunucu bilgileri
    """
    try:
        conn = get_redis_connection("default")
        info = conn.info()
        
        return {
            'version': info.get('redis_version', 'unknown'),
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', 'unknown'),
            'maxmemory_human': info.get('maxmemory_human', 'unlimited'),
            'uptime_in_days': info.get('uptime_in_days', 0),
            'keyspace': info.get('db0', {}),
        }
    except Exception as e:
        logger.error(f"Failed to get Redis info: {e}")
        return {}


def test_connection_pool():
    """
    Connection pool durumunu test et
    
    Returns:
        dict: Connection pool bilgileri
    """
    try:
        conn = get_redis_connection("default")
        pool = conn.connection_pool
        
        # Farklı pool tiplerini kontrol et
        pool_info = {
            'pool_type': type(pool).__name__,
            'max_connections': getattr(pool, 'max_connections', 'N/A'),
        }
        
        # BlockingConnectionPool için
        if hasattr(pool, '_created_connections'):
            pool_info['created_connections'] = pool._created_connections
        if hasattr(pool, '_in_use_connections'):
            pool_info['in_use'] = len(pool._in_use_connections)
        if hasattr(pool, '_available_connections'):
            pool_info['available'] = len(pool._available_connections)
            
        # Diğer pool tipleri için
        if hasattr(pool, 'connection_kwargs'):
            pool_info['connection_kwargs'] = {
                'host': pool.connection_kwargs.get('host', 'unknown'),
                'port': pool.connection_kwargs.get('port', 'unknown'),
                'db': pool.connection_kwargs.get('db', 'unknown'),
            }
            
        return pool_info
    except Exception as e:
        logger.error(f"Failed to get connection pool info: {e}")
        return {}


def clear_redis_cache(pattern='*'):
    """
    Redis cache'i temizle
    
    Args:
        pattern: Silinecek key pattern'i
    """
    try:
        cache.clear()
        logger.info(f"Redis cache cleared with pattern: {pattern}")
        return True
    except Exception as e:
        logger.error(f"Failed to clear Redis cache: {e}")
        return False