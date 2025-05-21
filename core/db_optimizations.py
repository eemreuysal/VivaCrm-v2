"""
VivaCRM v2 Database Optimizasyonları

Bu dosya, veritabanı performansını artırmak için kullanılacak optimizasyonları içerir.
"""
from django.db import models, connection
from django.db.models import Q, F, Count, Sum, Avg, Max, Min, Prefetch
from django.db.models.signals import post_save, post_delete, pre_save
from django.core.cache import cache
from django.conf import settings
from typing import Dict, List, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


# 1. Optimized Model Manager
class OptimizedManager(models.Manager):
    """
    Otomatik query optimizasyonu yapan model manager
    """
    
    def get_queryset(self):
        """Override to add default optimizations"""
        qs = super().get_queryset()
        
        # Model'e göre otomatik optimizasyon
        model_name = self.model.__name__
        
        # Default select_related ve prefetch_related
        if hasattr(self.model, 'default_select_related'):
            qs = qs.select_related(*self.model.default_select_related)
        
        if hasattr(self.model, 'default_prefetch_related'):
            qs = qs.prefetch_related(*self.model.default_prefetch_related)
        
        return qs
    
    def active(self):
        """Sadece aktif kayıtları getir"""
        return self.filter(is_active=True)
    
    def with_stats(self):
        """İstatistiklerle birlikte getir"""
        return self.annotate(
            total_orders=Count('orders'),
            total_revenue=Sum('orders__total'),
            avg_order_value=Avg('orders__total')
        )
    
    def recent(self, days=7):
        """Son N gün içindeki kayıtlar"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def by_user(self, user):
        """Kullanıcıya göre filtrele"""
        if hasattr(self.model, 'owner'):
            return self.filter(owner=user)
        elif hasattr(self.model, 'created_by'):
            return self.filter(created_by=user)
        return self.all()


# 2. Database Index Optimizer
class IndexOptimizer:
    """
    Veritabanı index'lerini optimize eden sınıf
    """
    
    @staticmethod
    def analyze_slow_queries():
        """Yavaş sorguları analiz et"""
        if connection.vendor != 'postgresql':
            return []
        
        with connection.cursor() as cursor:
            # PostgreSQL slow query log
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    max_time
                FROM pg_stat_statements
                WHERE mean_time > 100  -- 100ms'den yavaş
                ORDER BY mean_time DESC
                LIMIT 20
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'query': row[0],
                    'calls': row[1],
                    'total_time': row[2],
                    'mean_time': row[3],
                    'max_time': row[4]
                })
            
            return results
    
    @staticmethod
    def suggest_indexes(model):
        """Model için index önerileri"""
        suggestions = []
        
        # Foreign key alanları için index öner
        for field in model._meta.fields:
            if isinstance(field, models.ForeignKey) and not field.db_index:
                suggestions.append({
                    'field': field.name,
                    'type': 'btree',
                    'reason': 'Foreign key without index'
                })
        
        # Sık filtrelenen alanlar için index öner
        common_filter_fields = ['status', 'is_active', 'created_at', 'updated_at']
        for field_name in common_filter_fields:
            if hasattr(model, field_name):
                field = model._meta.get_field(field_name)
                if not field.db_index:
                    suggestions.append({
                        'field': field_name,
                        'type': 'btree',
                        'reason': 'Commonly filtered field'
                    })
        
        # Composite index önerileri
        if hasattr(model, 'Meta') and hasattr(model.Meta, 'index_together'):
            for fields in model.Meta.index_together:
                suggestions.append({
                    'fields': fields,
                    'type': 'composite',
                    'reason': 'Frequently queried together'
                })
        
        return suggestions
    
    @staticmethod
    def create_missing_indexes(model):
        """Eksik index'leri oluştur"""
        suggestions = IndexOptimizer.suggest_indexes(model)
        
        with connection.cursor() as cursor:
            for suggestion in suggestions:
                if suggestion['type'] == 'composite':
                    fields = suggestion['fields']
                    index_name = f"idx_{model._meta.db_table}_{'_'.join(fields)}"
                    
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {model._meta.db_table} ({', '.join(fields)})
                    """)
                else:
                    field = suggestion['field']
                    index_name = f"idx_{model._meta.db_table}_{field}"
                    
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {model._meta.db_table} ({field})
                    """)
        
        logger.info(f"Created {len(suggestions)} indexes for {model.__name__}")


# 3. Query Result Caching
class QueryCache:
    """
    Query sonuçlarını önbelleğe alan sınıf
    """
    
    def __init__(self, timeout=300):
        self.timeout = timeout
    
    def get_or_set(self, key, queryset, timeout=None):
        """Cache'den al veya yeni değer set et"""
        timeout = timeout or self.timeout
        
        # Cache'den kontrol et
        cached_result = cache.get(key)
        if cached_result is not None:
            return cached_result
        
        # Queryset'i evaluate et ve cache'le
        result = list(queryset)
        cache.set(key, result, timeout)
        
        return result
    
    def invalidate_model_cache(self, model):
        """Model cache'ini temizle"""
        cache_prefix = f"{model._meta.app_label}:{model._meta.model_name}"
        cache.delete_pattern(f"{cache_prefix}:*")
    
    @staticmethod
    def cache_key_for_queryset(queryset):
        """Queryset için benzersiz cache key oluştur"""
        import hashlib
        
        # SQL ve parametreleri al
        sql, params = queryset.query.sql_with_params()
        
        # Hash oluştur
        key_data = f"{sql}:{params}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        # Model bilgisi ile birleştir
        model = queryset.model
        return f"{model._meta.app_label}:{model._meta.model_name}:{key_hash}"


# 4. Batch Operations
class BatchOperations:
    """
    Toplu veritabanı işlemleri için optimizasyonlar
    """
    
    @staticmethod
    def bulk_create_with_batch(model, objects, batch_size=1000):
        """Batch'ler halinde bulk create"""
        created_objects = []
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            created = model.objects.bulk_create(batch, batch_size=batch_size)
            created_objects.extend(created)
            
            logger.info(f"Created batch {i//batch_size + 1} of {model.__name__}")
        
        return created_objects
    
    @staticmethod
    def bulk_update_with_batch(model, objects, fields, batch_size=1000):
        """Batch'ler halinde bulk update"""
        updated_count = 0
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            model.objects.bulk_update(batch, fields, batch_size=batch_size)
            updated_count += len(batch)
            
            logger.info(f"Updated batch {i//batch_size + 1} of {model.__name__}")
        
        return updated_count
    
    @staticmethod
    def chunked_delete(queryset, chunk_size=1000):
        """Chunk'lar halinde silme işlemi"""
        deleted_count = 0
        
        while True:
            # Chunk al
            chunk = list(queryset[:chunk_size])
            if not chunk:
                break
            
            # Chunk'ı sil
            for obj in chunk:
                obj.delete()
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} objects")
            
            # Rate limiting
            time.sleep(0.1)
        
        return deleted_count


# 5. Connection Pool Manager
class ConnectionPoolManager:
    """
    Veritabanı bağlantı havuzu yönetimi
    """
    
    @staticmethod
    def configure_pool(alias='default'):
        """Bağlantı havuzu ayarlarını yapılandır"""
        db_settings = settings.DATABASES[alias]
        
        # PostgreSQL için
        if db_settings['ENGINE'] == 'django.db.backends.postgresql':
            db_settings.setdefault('OPTIONS', {})
            db_settings['OPTIONS'].update({
                'connect_timeout': 10,
                'options': '-c statement_timeout=30000',  # 30 saniye
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
            })
            
            # Connection pooling
            db_settings['CONN_MAX_AGE'] = 600  # 10 dakika
    
    @staticmethod
    def get_connection_info():
        """Aktif bağlantı bilgilerini al"""
        if connection.vendor != 'postgresql':
            return {}
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    count(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            
            row = cursor.fetchone()
            return {
                'total': row[0],
                'active': row[1],
                'idle': row[2],
                'waiting': row[3]
            }


# 6. Database Vacuum and Analyze
class DatabaseMaintenance:
    """
    Veritabanı bakım işlemleri
    """
    
    @staticmethod
    def vacuum_analyze_table(model):
        """Tablo için VACUUM ve ANALYZE çalıştır"""
        if connection.vendor != 'postgresql':
            return
        
        table_name = model._meta.db_table
        
        with connection.cursor() as cursor:
            # VACUUM
            cursor.execute(f"VACUUM (ANALYZE, VERBOSE) {table_name}")
            logger.info(f"Vacuumed table: {table_name}")
    
    @staticmethod
    def analyze_table_stats(model):
        """Tablo istatistiklerini analiz et"""
        if connection.vendor != 'postgresql':
            return {}
        
        table_name = model._meta.db_table
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    n_mod_since_analyze as modifications_since_analyze,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public' AND tablename = %s
            """, [table_name])
            
            row = cursor.fetchone()
            if row:
                return {
                    'live_tuples': row[0],
                    'dead_tuples': row[1],
                    'modifications_since_analyze': row[2],
                    'last_vacuum': row[3],
                    'last_autovacuum': row[4],
                    'last_analyze': row[5],
                    'last_autoanalyze': row[6],
                    'bloat_ratio': row[1] / row[0] if row[0] > 0 else 0
                }
            
            return {}
    
    @staticmethod
    def optimize_all_tables():
        """Tüm tabloları optimize et"""
        from django.apps import apps
        
        for model in apps.get_models():
            if not model._meta.abstract:
                DatabaseMaintenance.vacuum_analyze_table(model)
                stats = DatabaseMaintenance.analyze_table_stats(model)
                
                # Bloat oranı yüksekse uyar
                if stats.get('bloat_ratio', 0) > 0.2:
                    logger.warning(
                        f"High bloat ratio for {model._meta.label}: "
                        f"{stats['bloat_ratio']:.2%}"
                    )


# 7. Query Performance Monitor
class QueryPerformanceMonitor:
    """
    Query performansını izleyen sınıf
    """
    
    def __init__(self):
        self.slow_query_threshold = 100  # 100ms
        self.queries = []
    
    def log_query(self, sql, duration):
        """Query'yi logla"""
        if duration > self.slow_query_threshold:
            self.queries.append({
                'sql': sql,
                'duration': duration,
                'timestamp': time.time()
            })
            
            # Yavaş query uyarısı
            logger.warning(
                f"Slow query detected ({duration}ms): {sql[:100]}..."
            )
    
    def get_slow_queries(self, limit=10):
        """En yavaş query'leri getir"""
        sorted_queries = sorted(
            self.queries, 
            key=lambda x: x['duration'], 
            reverse=True
        )
        return sorted_queries[:limit]
    
    def analyze_query_patterns(self):
        """Query pattern'lerini analiz et"""
        patterns = {}
        
        for query in self.queries:
            # Basit pattern çıkarma
            pattern = self._extract_pattern(query['sql'])
            
            if pattern not in patterns:
                patterns[pattern] = {
                    'count': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'max_duration': 0
                }
            
            patterns[pattern]['count'] += 1
            patterns[pattern]['total_duration'] += query['duration']
            patterns[pattern]['avg_duration'] = (
                patterns[pattern]['total_duration'] / 
                patterns[pattern]['count']
            )
            patterns[pattern]['max_duration'] = max(
                patterns[pattern]['max_duration'],
                query['duration']
            )
        
        return patterns
    
    def _extract_pattern(self, sql):
        """SQL'den pattern çıkar"""
        import re
        
        # Değerleri placeholder ile değiştir
        pattern = re.sub(r'\b\d+\b', '?', sql)
        pattern = re.sub(r"'[^']*'", '?', pattern)
        
        return pattern


# 8. Materialized View Manager
class MaterializedViewManager:
    """
    Materialized view yönetimi (PostgreSQL)
    """
    
    @staticmethod
    def create_materialized_view(name, query):
        """Materialized view oluştur"""
        if connection.vendor != 'postgresql':
            return
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {name} AS
                {query}
            """)
            
            # Index oluştur
            cursor.execute(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_{name}_id 
                ON {name} (id)
            """)
    
    @staticmethod
    def refresh_materialized_view(name, concurrently=True):
        """Materialized view'i yenile"""
        if connection.vendor != 'postgresql':
            return
        
        with connection.cursor() as cursor:
            concurrent = "CONCURRENTLY" if concurrently else ""
            cursor.execute(f"REFRESH MATERIALIZED VIEW {concurrent} {name}")
    
    @staticmethod
    def create_dashboard_views():
        """Dashboard için materialized view'ler oluştur"""
        views = {
            'mv_customer_stats': """
                SELECT 
                    c.id,
                    c.name,
                    COUNT(DISTINCT o.id) as order_count,
                    SUM(o.total) as total_revenue,
                    MAX(o.created_at) as last_order_date
                FROM customers_customer c
                LEFT JOIN orders_order o ON o.customer_id = c.id
                GROUP BY c.id, c.name
            """,
            
            'mv_product_performance': """
                SELECT 
                    p.id,
                    p.name,
                    p.category_id,
                    COUNT(DISTINCT oi.order_id) as order_count,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.quantity * oi.price) as total_revenue
                FROM products_product p
                LEFT JOIN orders_orderitem oi ON oi.product_id = p.id
                GROUP BY p.id, p.name, p.category_id
            """,
            
            'mv_daily_stats': """
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as order_count,
                    SUM(total) as revenue,
                    COUNT(DISTINCT customer_id) as unique_customers
                FROM orders_order
                WHERE status = 'completed'
                GROUP BY DATE(created_at)
            """
        }
        
        for view_name, query in views.items():
            MaterializedViewManager.create_materialized_view(view_name, query)


# 9. Database Health Monitor
class DatabaseHealthMonitor:
    """
    Veritabanı sağlık durumunu izleyen sınıf
    """
    
    @staticmethod
    def check_health():
        """Veritabanı sağlık kontrolü"""
        health_status = {
            'status': 'healthy',
            'issues': [],
            'metrics': {}
        }
        
        try:
            # Bağlantı kontrolü
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Bağlantı bilgileri
            conn_info = ConnectionPoolManager.get_connection_info()
            health_status['metrics']['connections'] = conn_info
            
            # Yavaş query kontrolü
            slow_queries = IndexOptimizer.analyze_slow_queries()
            if slow_queries:
                health_status['issues'].append({
                    'type': 'slow_queries',
                    'count': len(slow_queries),
                    'message': f"Found {len(slow_queries)} slow queries"
                })
            
            # Tablo bloat kontrolü
            from django.apps import apps
            for model in apps.get_models():
                if not model._meta.abstract:
                    stats = DatabaseMaintenance.analyze_table_stats(model)
                    if stats.get('bloat_ratio', 0) > 0.3:
                        health_status['issues'].append({
                            'type': 'table_bloat',
                            'table': model._meta.db_table,
                            'bloat_ratio': stats['bloat_ratio'],
                            'message': f"High bloat in {model._meta.label}"
                        })
            
            # Durumu belirle
            if health_status['issues']:
                health_status['status'] = 'warning'
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['issues'].append({
                'type': 'connection_error',
                'message': str(e)
            })
        
        return health_status


# 10. Query Hints and Optimization
class QueryHints:
    """
    Query optimizasyon ipuçları
    """
    
    @staticmethod
    def with_query_hints(queryset, hints):
        """Query'ye hint ekle (PostgreSQL)"""
        if connection.vendor != 'postgresql':
            return queryset
        
        # Raw SQL ile hint ekle
        sql, params = queryset.query.sql_with_params()
        
        # Hint'leri SQL'e ekle
        hint_sql = f"/*+ {' '.join(hints)} */ {sql}"
        
        # RawQuerySet döndür
        return queryset.model.objects.raw(hint_sql, params)
    
    @staticmethod
    def force_index(queryset, index_name):
        """Belirli bir index'i kullanmaya zorla"""
        return QueryHints.with_query_hints(
            queryset, 
            [f"INDEX({queryset.model._meta.db_table} {index_name})"]
        )
    
    @staticmethod
    def parallel_query(queryset, workers=4):
        """Parallel query execution (PostgreSQL 9.6+)"""
        return QueryHints.with_query_hints(
            queryset,
            [f"PARALLEL({workers})"]
        )