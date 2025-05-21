"""
VivaCRM v2 API Performans Optimizasyonları

Bu dosya, REST API performansını artırmak için kullanılacak optimizasyonları içerir.
"""
from rest_framework import serializers, viewsets, filters
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch, Q, Count, Sum, F, Avg
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from functools import wraps
import hashlib
import json
import time
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Cache için custom decorator
def cache_response(timeout, key_func=None):
    """Custom cache response decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                cache_key = f"{request.method}:{request.path}:{request.GET.urlencode()}"
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)
            
            # Get fresh response
            response = view_func(self, request, *args, **kwargs)
            
            # Cache the response data
            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
            
            return response
        return _wrapped_view
    return decorator


# 1. Optimized Pagination
class OptimizedPageNumberPagination(PageNumberPagination):
    """Optimize edilmiş sayfalama"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'results': data
        })


class OptimizedCursorPagination(CursorPagination):
    """Büyük veri setleri için cursor tabanlı sayfalama"""
    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    max_page_size = 200


# 2. Selective Field Serialization
class DynamicFieldsMixin:
    """
    Dinamik alan seçimi için mixin
    Kullanım: ?fields=id,name,email
    """
    
    def __init__(self, *args, **kwargs):
        # Hangi alanlar istenmiş?
        context = kwargs.get('context', {})
        request = context.get('request')
        fields = None
        
        if request:
            fields = request.query_params.get('fields')
            if fields:
                fields = fields.split(',')
        
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            # İstenmeyen alanları kaldır
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class OptimizedModelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Optimize edilmiş model serializer"""
    
    class Meta:
        abstract = True
    
    def to_representation(self, instance):
        """Gereksiz alan kontrollerini atla"""
        ret = super().to_representation(instance)
        
        # Boş değerleri kaldır (opsiyonel)
        if self.context.get('request'):
            exclude_nulls = self.context['request'].query_params.get('exclude_nulls')
            if exclude_nulls:
                ret = {k: v for k, v in ret.items() if v is not None}
        
        return ret


# 3. Query Optimization Mixin
class QueryOptimizationMixin:
    """ViewSet için query optimizasyon mixin'i"""
    
    # Model'e göre default optimizasyonlar
    select_related_fields = []
    prefetch_related_fields = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Select related
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
        
        # Prefetch related
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        
        # Dynamic prefetching based on requested fields
        if hasattr(self, 'request'):
            fields = self.request.query_params.get('fields')
            if fields:
                queryset = self._optimize_for_fields(queryset, fields.split(','))
        
        return queryset
    
    def _optimize_for_fields(self, queryset, fields):
        """İstenen alanlara göre optimize et"""
        # İlişkili alanları tespit et
        model = queryset.model
        for field in fields:
            if '__' in field:  # Nested field
                related_field = field.split('__')[0]
                if hasattr(model, related_field):
                    field_obj = model._meta.get_field(related_field)
                    if field_obj.is_relation:
                        if field_obj.many_to_one or field_obj.one_to_one:
                            queryset = queryset.select_related(related_field)
                        else:
                            queryset = queryset.prefetch_related(related_field)
        
        return queryset


# 4. Response Caching Decorator
def cache_response(timeout=300, key_func=None, cache_errors=False):
    """API response caching decorator"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Cache key oluştur
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                cache_key = _default_key_func(request, func.__name__)
            
            # Cache'den kontrol et
            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)
            
            # Response'u al
            response = func(self, request, *args, **kwargs)
            
            # Cache'e kaydet
            if response.status_code == 200 or (cache_errors and response.status_code < 500):
                cache.set(cache_key, response.data, timeout)
            
            return response
        
        return wrapper
    return decorator


def _default_key_func(request, view_name):
    """Default cache key generator"""
    # User bazlı cache key
    user_id = getattr(request.user, 'id', 'anonymous')
    
    # Query parameters
    query_params = request.query_params.dict()
    query_string = json.dumps(query_params, sort_keys=True)
    
    # Path ve method
    key_data = f"{view_name}:{request.method}:{request.path}:{user_id}:{query_string}"
    
    # Hash
    return f"api_cache:{hashlib.md5(key_data.encode()).hexdigest()}"


# 5. Batch Operations ViewSet
class BatchOperationsMixin:
    """Toplu işlemler için ViewSet mixin"""
    
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """Toplu oluşturma"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        # Batch create
        instances = self.perform_batch_create(serializer.validated_data)
        
        # Response
        response_serializer = self.get_serializer(instances, many=True)
        return Response(response_serializer.data, status=201)
    
    @action(detail=False, methods=['patch'])
    def batch_update(self, request):
        """Toplu güncelleme"""
        updates = request.data  # List of {id: ..., fields: ...}
        
        instances = []
        for update in updates:
            instance = self.get_queryset().get(pk=update['id'])
            serializer = self.get_serializer(
                instance, 
                data=update, 
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            instances.append(serializer.save())
        
        # Response
        response_serializer = self.get_serializer(instances, many=True)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['delete'])
    def batch_delete(self, request):
        """Toplu silme"""
        ids = request.data.get('ids', [])
        
        deleted_count = self.get_queryset().filter(pk__in=ids).delete()[0]
        
        return Response({'deleted': deleted_count})
    
    def perform_batch_create(self, validated_data):
        """Override this for custom batch create logic"""
        model = self.get_serializer().Meta.model
        return model.objects.bulk_create([
            model(**item) for item in validated_data
        ])


# 6. GraphQL-style Field Selection
class GraphQLStyleMixin:
    """GraphQL tarzı alan seçimi"""
    
    def get_serializer_class(self):
        """Dinamik serializer oluştur"""
        base_serializer = super().get_serializer_class()
        
        # Requested fields
        fields = self.request.query_params.get('fields')
        if not fields:
            return base_serializer
        
        fields = fields.split(',')
        
        # Create dynamic serializer
        class DynamicSerializer(base_serializer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
                # Only keep requested fields
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
        
        return DynamicSerializer


# 7. Async Support for DRF
import asyncio
from asgiref.sync import sync_to_async

class AsyncViewSetMixin:
    """Async support for ViewSets"""
    
    async def alist(self, request, *args, **kwargs):
        """Async list action"""
        queryset = await sync_to_async(self.filter_queryset)(self.get_queryset())
        
        page = await sync_to_async(self.paginate_queryset)(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return await sync_to_async(self.get_paginated_response)(data)
        
        serializer = self.get_serializer(queryset, many=True)
        data = await sync_to_async(lambda: serializer.data)()
        return Response(data)
    
    async def aretrieve(self, request, *args, **kwargs):
        """Async retrieve action"""
        instance = await sync_to_async(self.get_object)()
        serializer = self.get_serializer(instance)
        data = await sync_to_async(lambda: serializer.data)()
        return Response(data)


# 8. Compression and ETags
class CompressionMixin:
    """Response compression ve ETag support"""
    
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Add ETag
        if response.status_code == 200:
            import hashlib
            
            # Calculate ETag from response content
            content = json.dumps(response.data, sort_keys=True)
            etag = hashlib.md5(content.encode()).hexdigest()
            response['ETag'] = f'"{etag}"'
            
            # Check If-None-Match
            if request.META.get('HTTP_IF_NONE_MATCH') == f'"{etag}"':
                response.status_code = 304
                response.content = ''
        
        return response


# 9. API Rate Limiting
from rest_framework.throttling import BaseThrottle

class DynamicRateThrottle(BaseThrottle):
    """Kullanıcı tipine göre dinamik rate limiting"""
    
    rates = {
        'anonymous': '100/hour',
        'authenticated': '1000/hour',
        'premium': '5000/hour',
        'admin': None  # No limit
    }
    
    def get_rate(self):
        if not hasattr(self.request, 'user'):
            return self.parse_rate(self.rates['anonymous'])
        
        user = self.request.user
        
        if user.is_superuser:
            return None
        elif hasattr(user, 'is_premium') and user.is_premium:
            return self.parse_rate(self.rates['premium'])
        elif user.is_authenticated:
            return self.parse_rate(self.rates['authenticated'])
        else:
            return self.parse_rate(self.rates['anonymous'])


# 10. Optimized ViewSet Example (Örnek kullanım)
# Bu örnek kod, optimize edilmiş ViewSet nasıl oluşturulacağını gösterir
"""
class OptimizedProductViewSet(
    QueryOptimizationMixin,
    BatchOperationsMixin,
    CompressionMixin,
    viewsets.ModelViewSet
):
    # Tam optimize edilmiş ViewSet örneği
    
    serializer_class = ProductSerializer
    pagination_class = OptimizedPageNumberPagination
    throttle_classes = [DynamicRateThrottle]
    
    # Query optimizations
"""
"""
    select_related_fields = ['category', 'created_by']
    prefetch_related_fields = ['images', 'reviews']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtering
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Searching
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Sorting
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Annotations
        if self.request.query_params.get('with_stats'):
            queryset = queryset.annotate(
                review_count=Count('reviews'),
                avg_rating=Avg('reviews__rating'),
                total_sales=Sum('orderitem__quantity')
            )
        
        return queryset
    
    @method_decorator(cache_page(60*15))  # 15 dakika
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        # Cache'li liste endpoint'i
        return super().list(request, *args, **kwargs)
    
    @cache_response(timeout=300)
    def retrieve(self, request, *args, **kwargs):
        # Cache'li detay endpoint'i
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    @cache_response(timeout=3600)  # 1 saat
    def popular(self, request):
        # Popüler ürünler - yoğun cache
        queryset = self.get_queryset().annotate(
            order_count=Count('orderitem')
        ).order_by('-order_count')[:20]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    @cache_response(timeout=1800, key_func=lambda r, *a, **k: f"product_stats:{k['pk']}")
    def stats(self, request, pk=None):
        # Ürün istatistikleri
        product = self.get_object()
        
        stats = {
            'total_orders': product.orderitem_set.count(),
            'total_quantity': product.orderitem_set.aggregate(
                total=Sum('quantity')
            )['total'] or 0,
            'revenue': product.orderitem_set.aggregate(
                total=Sum(F('quantity') * F('price'))
            )['total'] or 0,
            'avg_rating': product.reviews.aggregate(
                avg=Avg('rating')
            )['avg'] or 0,
            'review_count': product.reviews.count()
        }
        
        return Response(stats)
"""


# 11. API Performance Middleware
class APIPerformanceMiddleware:
    """API performans monitoring middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only for API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Start timing
        start_time = time.time()
        
        # Query count before
        from django.db import connection
        queries_before = len(connection.queries)
        
        # Process request
        response = self.get_response(request)
        
        # Calculate metrics
        duration = time.time() - start_time
        query_count = len(connection.queries) - queries_before
        
        # Add headers
        response['X-Response-Time'] = f"{duration:.3f}s"
        response['X-Query-Count'] = str(query_count)
        response['X-Query-Time'] = f"{sum(float(q['time']) for q in connection.queries[queries_before:])}s"
        
        # Log slow APIs
        if duration > 1.0:  # 1 second
            logger.warning(
                f"Slow API: {request.method} {request.path} "
                f"took {duration:.3f}s with {query_count} queries"
            )
        
        return response