"""
VivaCRM v2 Performans İzleme ve Metrikler

Bu dosya, performans izleme ve metrik toplama sisteminin nasıl kurulacağına dair örnekler içerir.
"""
import time
import psutil
import logging
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List


# 1. Performans Metrikleri Toplayıcı
class PerformanceCollector:
    """Sistem performans metriklerini toplar"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance.collector')
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Sistem seviyesinde metrikleri topla"""
        return {
            'timestamp': timezone.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'freq': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used,
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent,
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv,
            }
        }
    
    def collect_django_metrics(self) -> Dict[str, Any]:
        """Django seviyesinde metrikleri topla"""
        from django.contrib.sessions.models import Session
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        return {
            'timestamp': timezone.now().isoformat(),
            'database': self._collect_database_metrics(),
            'cache': self._collect_cache_metrics(),
            'sessions': {
                'active': Session.objects.filter(
                    expire_date__gte=timezone.now()
                ).count(),
                'total': Session.objects.count(),
            },
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'staff': User.objects.filter(is_staff=True).count(),
                'superusers': User.objects.filter(is_superuser=True).count(),
            }
        }
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Veritabanı metriklerini topla"""
        with connection.cursor() as cursor:
            # PostgreSQL özel sorguları
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT 
                        pg_database_size(current_database()) as size,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT count(*) FROM pg_stat_activity) as total_connections,
                        (SELECT count(*) FROM pg_stat_user_tables) as table_count
                """)
                result = cursor.fetchone()
                return {
                    'size': result[0],
                    'active_connections': result[1],
                    'total_connections': result[2],
                    'table_count': result[3],
                }
            else:
                return {}
    
    def _collect_cache_metrics(self) -> Dict[str, Any]:
        """Cache metriklerini topla"""
        # Redis cache metrikleri
        if hasattr(cache, '_cache'):
            backend = cache._cache
            if hasattr(backend, 'get_stats'):
                return backend.get_stats()
        
        # Basit metrikler
        return {
            'backend': settings.CACHES['default']['BACKEND'],
            'location': settings.CACHES['default'].get('LOCATION', ''),
        }
    
    def collect_business_metrics(self) -> Dict[str, Any]:
        """İş metrikleri topla"""
        from orders.models import Order
        from products.models import Product
        from customers.models import Customer
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        return {
            'timestamp': timezone.now().isoformat(),
            'orders': {
                'today': Order.objects.filter(created_at__date=today).count(),
                'yesterday': Order.objects.filter(created_at__date=yesterday).count(),
                'last_week': Order.objects.filter(created_at__date__gte=last_week).count(),
                'last_month': Order.objects.filter(created_at__date__gte=last_month).count(),
                'total': Order.objects.count(),
                'pending': Order.objects.filter(status='pending').count(),
                'completed': Order.objects.filter(status='completed').count(),
            },
            'revenue': {
                'today': float(Order.objects.filter(
                    created_at__date=today,
                    status='completed'
                ).aggregate(total=Sum('total'))['total'] or 0),
                'yesterday': float(Order.objects.filter(
                    created_at__date=yesterday,
                    status='completed'
                ).aggregate(total=Sum('total'))['total'] or 0),
                'last_week': float(Order.objects.filter(
                    created_at__date__gte=last_week,
                    status='completed'
                ).aggregate(total=Sum('total'))['total'] or 0),
                'last_month': float(Order.objects.filter(
                    created_at__date__gte=last_month,
                    status='completed'
                ).aggregate(total=Sum('total'))['total'] or 0),
            },
            'products': {
                'total': Product.objects.count(),
                'active': Product.objects.filter(is_active=True).count(),
                'out_of_stock': Product.objects.filter(stock=0).count(),
                'low_stock': Product.objects.filter(
                    stock__gt=0,
                    stock__lte=F('threshold_stock')
                ).count(),
            },
            'customers': {
                'total': Customer.objects.count(),
                'active': Customer.objects.filter(is_active=True).count(),
                'new_today': Customer.objects.filter(created_at__date=today).count(),
                'new_this_week': Customer.objects.filter(created_at__date__gte=last_week).count(),
            },
        }


# 2. Performans Raporu Oluşturucu
class PerformanceReporter:
    """Performans raporları oluşturur"""
    
    def __init__(self):
        self.collector = PerformanceCollector()
        self.logger = logging.getLogger('performance.reporter')
    
    def generate_hourly_report(self) -> Dict[str, Any]:
        """Saatlik performans raporu"""
        return {
            'report_type': 'hourly',
            'generated_at': timezone.now().isoformat(),
            'period': {
                'start': (timezone.now() - timedelta(hours=1)).isoformat(),
                'end': timezone.now().isoformat(),
            },
            'metrics': {
                'system': self.collector.collect_system_metrics(),
                'django': self.collector.collect_django_metrics(),
                'business': self.collector.collect_business_metrics(),
            }
        }
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Günlük performans raporu"""
        return {
            'report_type': 'daily',
            'generated_at': timezone.now().isoformat(),
            'period': {
                'start': (timezone.now() - timedelta(days=1)).isoformat(),
                'end': timezone.now().isoformat(),
            },
            'metrics': self._aggregate_daily_metrics(),
            'alerts': self._check_performance_alerts(),
        }
    
    def _aggregate_daily_metrics(self) -> Dict[str, Any]:
        """Günlük metrikleri topla"""
        # Cache'den son 24 saatin metriklerini al
        metrics = []
        for i in range(24):
            key = f"metrics:hourly:{(timezone.now() - timedelta(hours=i)).strftime('%Y%m%d%H')}"
            metric = cache.get(key)
            if metric:
                metrics.append(metric)
        
        # Ortalama hesapla
        if metrics:
            return {
                'average_cpu': sum(m['system']['cpu']['percent'] for m in metrics) / len(metrics),
                'average_memory': sum(m['system']['memory']['percent'] for m in metrics) / len(metrics),
                'total_orders': sum(m['business']['orders']['today'] for m in metrics),
                'total_revenue': sum(m['business']['revenue']['today'] for m in metrics),
            }
        
        return {}
    
    def _check_performance_alerts(self) -> List[Dict[str, Any]]:
        """Performans uyarılarını kontrol et"""
        alerts = []
        
        # CPU kullanımı yüksek mi?
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'cpu_high',
                'message': f'CPU kullanımı çok yüksek: {cpu_percent}%',
                'value': cpu_percent,
            })
        elif cpu_percent > 75:
            alerts.append({
                'level': 'warning',
                'type': 'cpu_high',
                'message': f'CPU kullanımı yüksek: {cpu_percent}%',
                'value': cpu_percent,
            })
        
        # Bellek kullanımı yüksek mi?
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'memory_high',
                'message': f'Bellek kullanımı çok yüksek: {memory_percent}%',
                'value': memory_percent,
            })
        elif memory_percent > 80:
            alerts.append({
                'level': 'warning',
                'type': 'memory_high',
                'message': f'Bellek kullanımı yüksek: {memory_percent}%',
                'value': memory_percent,
            })
        
        # Disk kullanımı yüksek mi?
        disk_percent = psutil.disk_usage('/').percent
        if disk_percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'disk_high',
                'message': f'Disk kullanımı çok yüksek: {disk_percent}%',
                'value': disk_percent,
            })
        elif disk_percent > 80:
            alerts.append({
                'level': 'warning',
                'type': 'disk_high',
                'message': f'Disk kullanımı yüksek: {disk_percent}%',
                'value': disk_percent,
            })
        
        return alerts


# 3. Performans İzleme Management Command
class Command(BaseCommand):
    """
    Django management command for performance monitoring
    
    Usage:
        python manage.py monitor_performance --type=realtime
        python manage.py monitor_performance --type=report --period=daily
    """
    
    help = 'Monitor system and application performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['realtime', 'report'],
            default='realtime',
            help='Type of monitoring'
        )
        parser.add_argument(
            '--period',
            choices=['hourly', 'daily', 'weekly'],
            default='hourly',
            help='Report period'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds'
        )
    
    def handle(self, *args, **options):
        monitor_type = options['type']
        
        if monitor_type == 'realtime':
            self.monitor_realtime(options['interval'])
        else:
            self.generate_report(options['period'])
    
    def monitor_realtime(self, interval):
        """Gerçek zamanlı performans izleme"""
        collector = PerformanceCollector()
        
        self.stdout.write('Starting real-time performance monitoring...')
        
        try:
            while True:
                metrics = {
                    'system': collector.collect_system_metrics(),
                    'django': collector.collect_django_metrics(),
                }
                
                # Konsola yazdır
                self.stdout.write(f"\n{'-' * 50}")
                self.stdout.write(f"Time: {metrics['system']['timestamp']}")
                self.stdout.write(f"CPU: {metrics['system']['cpu']['percent']}%")
                self.stdout.write(f"Memory: {metrics['system']['memory']['percent']}%")
                self.stdout.write(f"Disk: {metrics['system']['disk']['percent']}%")
                
                # Cache'e kaydet
                cache_key = f"metrics:realtime:{datetime.now().strftime('%Y%m%d%H%M%S')}"
                cache.set(cache_key, metrics, timeout=3600)
                
                # Bekle
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write('\nStopping monitoring...')
    
    def generate_report(self, period):
        """Performans raporu oluştur"""
        reporter = PerformanceReporter()
        
        if period == 'hourly':
            report = reporter.generate_hourly_report()
        elif period == 'daily':
            report = reporter.generate_daily_report()
        else:
            self.stdout.write(self.style.ERROR(f'Unsupported period: {period}'))
            return
        
        # Raporu yazdır
        self.stdout.write(json.dumps(report, indent=2))
        
        # Raporu kaydet
        report_file = f"reports/performance_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f'Report saved to: {report_file}'))


# 4. Grafana Dashboard Config
GRAFANA_DASHBOARD_CONFIG = {
    "dashboard": {
        "title": "VivaCRM Performance Dashboard",
        "panels": [
            {
                "title": "CPU Usage",
                "type": "graph",
                "targets": [
                    {
                        "metric": "vivacrm.system.cpu.percent",
                        "aggregation": "avg",
                    }
                ],
            },
            {
                "title": "Memory Usage",
                "type": "graph",
                "targets": [
                    {
                        "metric": "vivacrm.system.memory.percent",
                        "aggregation": "avg",
                    }
                ],
            },
            {
                "title": "Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "metric": "vivacrm.requests.count",
                        "aggregation": "rate",
                    }
                ],
            },
            {
                "title": "Response Time",
                "type": "graph",
                "targets": [
                    {
                        "metric": "vivacrm.requests.duration",
                        "aggregation": "avg",
                    }
                ],
            },
            {
                "title": "Database Queries",
                "type": "graph",
                "targets": [
                    {
                        "metric": "vivacrm.database.queries.count",
                        "aggregation": "sum",
                    }
                ],
            },
            {
                "title": "Cache Hit Rate",
                "type": "graph",
                "targets": [
                    {
                        "metric": "vivacrm.cache.hit_rate",
                        "aggregation": "avg",
                    }
                ],
            },
            {
                "title": "Orders",
                "type": "stat",
                "targets": [
                    {
                        "metric": "vivacrm.business.orders.count",
                        "aggregation": "sum",
                    }
                ],
            },
            {
                "title": "Revenue",
                "type": "stat",
                "targets": [
                    {
                        "metric": "vivacrm.business.revenue.total",
                        "aggregation": "sum",
                    }
                ],
            },
        ],
    },
}


# 5. Prometheus Exporter
class PrometheusExporter:
    """Prometheus için metrik exporter"""
    
    def __init__(self):
        self.collector = PerformanceCollector()
    
    def export_metrics(self) -> str:
        """Prometheus formatında metrikler"""
        metrics = []
        
        # Sistem metrikleri
        system_metrics = self.collector.collect_system_metrics()
        metrics.append(f"vivacrm_cpu_percent {system_metrics['cpu']['percent']}")
        metrics.append(f"vivacrm_memory_percent {system_metrics['memory']['percent']}")
        metrics.append(f"vivacrm_disk_percent {system_metrics['disk']['percent']}")
        
        # Django metrikleri
        django_metrics = self.collector.collect_django_metrics()
        metrics.append(f"vivacrm_sessions_active {django_metrics['sessions']['active']}")
        metrics.append(f"vivacrm_users_total {django_metrics['users']['total']}")
        
        # İş metrikleri
        business_metrics = self.collector.collect_business_metrics()
        metrics.append(f"vivacrm_orders_total {business_metrics['orders']['total']}")
        metrics.append(f"vivacrm_revenue_total {business_metrics['revenue']['last_month']}")
        
        return '\n'.join(metrics)