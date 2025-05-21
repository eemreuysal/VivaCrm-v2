"""
Redis Monitoring Middleware
Redis bağlantı sayısını ve performansını izler
"""
from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
import time
import logging

logger = logging.getLogger(__name__)


class RedisMonitorMiddleware(MiddlewareMixin):
    """
    Her request'te Redis bağlantı durumunu kontrol eder
    """
    
    def process_request(self, request):
        """Request başlangıcında Redis durumunu logla"""
        request._redis_start_time = time.time()
        
        if hasattr(request, 'user') and request.user.is_staff:
            try:
                conn = get_redis_connection("default")
                info = conn.info()
                logger.debug(f"Redis connections: {info.get('connected_clients', 0)}")
            except Exception as e:
                logger.error(f"Redis monitoring error: {e}")
    
    def process_response(self, request, response):
        """Response sonunda Redis performansını logla"""
        if hasattr(request, '_redis_start_time'):
            duration = time.time() - request._redis_start_time
            if duration > 1:  # 1 saniyeden uzun süren işlemler
                logger.warning(f"Slow Redis operation: {duration:.2f} seconds")
        
        # Debug header ekle (sadece staff users için)
        if hasattr(request, 'user') and request.user.is_staff:
            try:
                conn = get_redis_connection("default")
                pool = conn.connection_pool
                response['X-Redis-Pool-Size'] = f"{len(pool._in_use_connections)}/{pool.max_connections}"
            except:
                pass
        
        return response