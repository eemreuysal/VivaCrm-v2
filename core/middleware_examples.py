"""
VivaCRM v2 Middleware Kullanım Örnekleri

Bu dosya, projede middleware'lerin nasıl kullanılacağına dair örnekler içerir.
"""
import time
import logging
import json
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.utils import timezone


# 1. Response Compression Middleware
class CompressionMiddleware:
    """Response sıkıştırma middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.min_size = 1024  # 1KB minimum
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Text tabanlı içerikleri sıkıştır
        if self._should_compress(request, response):
            import gzip
            
            compressed_content = gzip.compress(
                response.content,
                compresslevel=6  # Orta seviye sıkıştırma
            )
            
            # Sıkıştırma faydalıysa uygula
            if len(compressed_content) < len(response.content):
                response.content = compressed_content
                response['Content-Encoding'] = 'gzip'
                response['Content-Length'] = str(len(compressed_content))
        
        return response
    
    def _should_compress(self, request, response):
        """Sıkıştırma yapılmalı mı?"""
        # Client gzip destekliyor mu?
        if 'gzip' not in request.META.get('HTTP_ACCEPT_ENCODING', ''):
            return False
        
        # Response boyutu yeterli mi?
        if len(response.content) < self.min_size:
            return False
        
        # Content type uygun mu?
        content_type = response.get('Content-Type', '')
        compressible_types = [
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'application/xml',
        ]
        
        return any(t in content_type for t in compressible_types)


# 2. Request Throttling Middleware
class ThrottlingMiddleware:
    """İstek sınırlama middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = 100  # Dakikada maksimum istek
        self.window = 60  # 60 saniye pencere
    
    def __call__(self, request):
        # IP adresini al
        ip = self._get_client_ip(request)
        
        # Rate limiting anahtarı
        key = f"rate_limit:{ip}"
        
        # Mevcut sayacı al
        count = cache.get(key, 0)
        
        # Limit aşıldı mı?
        if count >= self.rate_limit:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': self.window
            }, status=429)
        
        # Sayacı artır
        cache.set(key, count + 1, timeout=self.window)
        
        # İsteği işle
        response = self.get_response(request)
        
        # Rate limit bilgilerini header'a ekle
        response['X-RateLimit-Limit'] = str(self.rate_limit)
        response['X-RateLimit-Remaining'] = str(self.rate_limit - count - 1)
        response['X-RateLimit-Reset'] = str(int(time.time()) + self.window)
        
        return response
    
    def _get_client_ip(self, request):
        """Client IP adresini al"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# 3. Performance Profiling Middleware
class ProfilingMiddleware:
    """Detaylı performans profiling middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('performance')
    
    def __call__(self, request):
        # Profiling başlat
        if settings.DEBUG and request.GET.get('profile') == '1':
            import cProfile
            import pstats
            from io import StringIO
            
            profiler = cProfile.Profile()
            profiler.enable()
        else:
            profiler = None
        
        # Metrikleri topla
        start_time = time.time()
        start_queries = len(connection.queries) if settings.DEBUG else 0
        
        # İsteği işle
        response = self.get_response(request)
        
        # Metrikleri hesapla
        duration = time.time() - start_time
        query_count = len(connection.queries) - start_queries if settings.DEBUG else 0
        
        # Profiling sonuçları
        if profiler:
            profiler.disable()
            s = StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 fonksiyon
            
            # Sonuçları response'a ekle
            profile_data = s.getvalue()
            response['X-Profile-Data'] = profile_data[:1000]  # İlk 1000 karakter
        
        # Performans logları
        self.logger.info({
            'path': request.path,
            'method': request.method,
            'duration': duration,
            'query_count': query_count,
            'user': getattr(request.user, 'username', 'anonymous'),
            'status_code': response.status_code,
            'content_length': len(response.content) if hasattr(response, 'content') else 0,
        })
        
        # Response header'ları
        response['X-Response-Time'] = f"{duration:.3f}s"
        response['X-Query-Count'] = str(query_count)
        
        return response


# 4. Security Headers Middleware
class SecurityHeadersMiddleware:
    """Güvenlik header'ları middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Güvenlik header'ları ekle
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (sadece HTTPS'de)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # CSP (Content Security Policy)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "img-src 'self' data: https:",
            "font-src 'self' https://cdn.jsdelivr.net",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        return response


# 5. Correlation ID Middleware
class CorrelationIdMiddleware:
    """İstek takibi için correlation ID middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import uuid
        
        # Correlation ID al veya oluştur
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Request'e ekle
        request.correlation_id = correlation_id
        
        # İsteği işle
        response = self.get_response(request)
        
        # Response'a ekle
        response['X-Correlation-ID'] = correlation_id
        
        return response


# 6. Database Connection Pool Middleware
class DatabasePoolMiddleware:
    """Veritabanı bağlantı havuzu middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Bağlantı havuzu kontrolü
        from django.db import connections
        
        for conn in connections.all():
            # Bağlantı havuzu ayarları
            conn.settings_dict.setdefault('CONN_MAX_AGE', 600)
            conn.settings_dict.setdefault('OPTIONS', {})
            conn.settings_dict['OPTIONS'].setdefault('MAX_CONNS', 50)
            conn.settings_dict['OPTIONS'].setdefault('MIN_CONNS', 2)
        
        # İsteği işle
        response = self.get_response(request)
        
        # Bağlantı istatistikleri
        if settings.DEBUG:
            for alias, conn in connections.items():
                queries = len(conn.queries)
                response[f'X-DB-{alias}-Queries'] = str(queries)
        
        return response


# 7. API Version Middleware
class APIVersionMiddleware:
    """API versiyon yönetimi middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.default_version = 'v1'
        self.supported_versions = ['v1', 'v2']
    
    def __call__(self, request):
        # API path'i mi?
        if request.path.startswith('/api/'):
            # Version'ı header'dan al
            version = request.headers.get('API-Version', self.default_version)
            
            # URL'den version al
            path_parts = request.path.split('/')
            if len(path_parts) > 2 and path_parts[2] in self.supported_versions:
                version = path_parts[2]
            
            # Desteklenmeyen version
            if version not in self.supported_versions:
                return JsonResponse({
                    'error': 'Unsupported API version',
                    'supported_versions': self.supported_versions
                }, status=400)
            
            # Request'e version ekle
            request.api_version = version
        
        # İsteği işle
        response = self.get_response(request)
        
        # API response'larına version ekle
        if request.path.startswith('/api/'):
            response['API-Version'] = getattr(request, 'api_version', self.default_version)
        
        return response


# 8. Request/Response Logging Middleware
class LoggingMiddleware:
    """Detaylı request/response loglama middleware'i"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('vivacrm.requests')
        self.exclude_paths = ['/health/', '/metrics/']
    
    def __call__(self, request):
        # Excluded path kontrolü
        if any(request.path.startswith(p) for p in self.exclude_paths):
            return self.get_response(request)
        
        # Request zamanı
        request._start_time = time.time()
        
        # Request logu
        request_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'user': getattr(request.user, 'username', 'anonymous'),
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # POST data (hassas bilgileri filtrele)
        if request.method == 'POST':
            try:
                body = json.loads(request.body)
                # Şifre gibi hassas alanları filtrele
                filtered_body = self._filter_sensitive_data(body)
                request_data['body'] = filtered_body
            except:
                request_data['body'] = '<not-json>'
        
        self.logger.info(f"Request: {json.dumps(request_data)}")
        
        # İsteği işle
        response = self.get_response(request)
        
        # Response logu
        duration = time.time() - request._start_time
        response_data = {
            'timestamp': timezone.now().isoformat(),
            'duration': duration,
            'status_code': response.status_code,
            'content_length': len(response.content) if hasattr(response, 'content') else 0,
        }
        
        self.logger.info(f"Response: {json.dumps(response_data)}")
        
        return response
    
    def _get_client_ip(self, request):
        """Client IP adresini al"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _filter_sensitive_data(self, data):
        """Hassas verileri filtrele"""
        sensitive_keys = ['password', 'token', 'secret', 'api_key']
        
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if any(s in key.lower() for s in sensitive_keys):
                    filtered[key] = '***FILTERED***'
                else:
                    filtered[key] = self._filter_sensitive_data(value)
            return filtered
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        else:
            return data


# Settings.py'de Middleware Sıralaması
"""
MIDDLEWARE = [
    # Django güvenlik middleware'leri en üstte
    'django.middleware.security.SecurityMiddleware',
    
    # Compression middleware (response'dan önce)
    'core.middleware_examples.CompressionMiddleware',
    
    # Session middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # CORS headers (varsa)
    'corsheaders.middleware.CorsMiddleware',
    
    # Common middleware
    'django.middleware.common.CommonMiddleware',
    
    # CSRF protection
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # Authentication
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Messages
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Clickjacking protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom middlewares
    'core.middleware_examples.ThrottlingMiddleware',
    'core.middleware_examples.APIVersionMiddleware',
    'core.middleware_examples.CorrelationIdMiddleware',
    'core.middleware.PerformanceMonitoringMiddleware',
    'core.middleware.QueryCountMiddleware',
    'core.middleware_examples.SecurityHeadersMiddleware',
    'core.middleware_examples.ProfilingMiddleware',
    'core.middleware_examples.LoggingMiddleware',
    
    # Cache middleware (en sonda)
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]
"""