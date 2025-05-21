"""
Monitoring and alerting module for VivaCRM v2.
Handles performance metrics, system health checks, and alerts.
"""
import time
import psutil
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import get_user_model
from celery import shared_task
import json

User = get_user_model()
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system resources and performance metrics."""
    
    @staticmethod
    def get_cpu_usage():
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=1)
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage."""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'used': memory.used,
            'available': memory.available,
            'percent': memory.percent
        }
    
    @staticmethod
    def get_disk_usage():
        """Get disk usage for the main partition."""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    
    @staticmethod
    def get_database_status():
        """Check database connection and performance."""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            query_time = time.time() - start_time
            
            # Get database size
            cursor.execute("""
                SELECT 
                    pg_database_size(current_database()) as size,
                    count(*) as connection_count
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            db_info = cursor.fetchone()
            
            return {
                'status': 'healthy',
                'query_time': query_time,
                'size': db_info[0] if db_info else 0,
                'connections': db_info[1] if db_info else 0
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def get_cache_status():
        """Check cache connection and stats."""
        try:
            # Test cache connection
            cache_key = f'health_check_{time.time()}'
            cache.set(cache_key, 'test', 5)
            value = cache.get(cache_key)
            cache.delete(cache_key)
            
            if value != 'test':
                raise Exception("Cache read/write test failed")
            
            # Get cache stats (if Redis)
            stats = {}
            if hasattr(cache._cache, 'get_stats'):
                stats = cache._cache.get_stats()
            
            return {
                'status': 'healthy',
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


class MetricsCollector:
    """Collect and store application metrics."""
    
    METRICS_PREFIX = 'metrics:'
    RETENTION_DAYS = 7
    
    @classmethod
    def record_metric(cls, metric_name, value, timestamp=None):
        """Record a metric value."""
        if timestamp is None:
            timestamp = timezone.now()
        
        # Store in cache with TTL
        cache_key = f"{cls.METRICS_PREFIX}{metric_name}:{timestamp.timestamp()}"
        cache.set(cache_key, value, cls.RETENTION_DAYS * 24 * 60 * 60)
        
        # Also update current value
        current_key = f"{cls.METRICS_PREFIX}{metric_name}:current"
        cache.set(current_key, value, 300)  # 5 minutes
    
    @classmethod
    def get_metric(cls, metric_name, start_time=None, end_time=None):
        """Get metric values for a time range."""
        if start_time is None:
            start_time = timezone.now() - timedelta(hours=1)
        if end_time is None:
            end_time = timezone.now()
        
        # Get all keys for this metric
        pattern = f"{cls.METRICS_PREFIX}{metric_name}:*"
        keys = cache.keys(pattern)
        
        values = []
        for key in keys:
            # Extract timestamp from key
            try:
                timestamp_str = key.split(':')[-1]
                if timestamp_str == 'current':
                    continue
                    
                timestamp = float(timestamp_str)
                metric_time = datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())
                
                if start_time <= metric_time <= end_time:
                    value = cache.get(key)
                    if value is not None:
                        values.append({
                            'timestamp': metric_time.isoformat(),
                            'value': value
                        })
            except (ValueError, IndexError):
                continue
        
        return sorted(values, key=lambda x: x['timestamp'])
    
    @classmethod
    def get_current_metrics(cls):
        """Get all current metric values."""
        pattern = f"{cls.METRICS_PREFIX}*:current"
        keys = cache.keys(pattern)
        
        metrics = {}
        for key in keys:
            metric_name = key.replace(cls.METRICS_PREFIX, '').replace(':current', '')
            value = cache.get(key)
            if value is not None:
                metrics[metric_name] = value
        
        return metrics


class AlertManager:
    """Manage system alerts and notifications."""
    
    ALERT_PREFIX = 'alert:'
    ALERT_COOLDOWN = 300  # 5 minutes between same alerts
    
    @classmethod
    def send_alert(cls, alert_type, message, severity='warning', extra_data=None):
        """Send an alert if not recently sent."""
        # Check cooldown
        cooldown_key = f"{cls.ALERT_PREFIX}cooldown:{alert_type}"
        if cache.get(cooldown_key):
            logger.info(f"Alert {alert_type} in cooldown period")
            return False
        
        # Set cooldown
        cache.set(cooldown_key, True, cls.ALERT_COOLDOWN)
        
        # Store alert
        alert_data = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': timezone.now().isoformat(),
            'extra_data': extra_data or {}
        }
        
        alert_key = f"{cls.ALERT_PREFIX}{alert_type}:{timezone.now().timestamp()}"
        cache.set(alert_key, alert_data, 86400)  # Keep for 24 hours
        
        # Send notifications based on severity
        if severity in ['critical', 'error']:
            cls._send_email_alert(alert_data)
        
        # Log the alert
        logger.warning(f"Alert: {alert_type} - {message}")
        
        return True
    
    @classmethod
    def _send_email_alert(cls, alert_data):
        """Send email notification for critical alerts."""
        try:
            admins = User.objects.filter(is_superuser=True, is_active=True)
            admin_emails = list(admins.values_list('email', flat=True))
            
            if not admin_emails:
                return
            
            subject = f"VivaCRM Alert: {alert_data['type']}"
            message = f"""
Alert Type: {alert_data['type']}
Severity: {alert_data['severity']}
Time: {alert_data['timestamp']}

Message:
{alert_data['message']}

Extra Data:
{json.dumps(alert_data['extra_data'], indent=2)}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")


# Celery tasks for periodic monitoring
@shared_task
def collect_system_metrics():
    """Collect system metrics periodically."""
    try:
        # CPU usage
        cpu_usage = SystemMonitor.get_cpu_usage()
        MetricsCollector.record_metric('system.cpu.usage', cpu_usage)
        
        # Memory usage
        memory = SystemMonitor.get_memory_usage()
        MetricsCollector.record_metric('system.memory.usage', memory['percent'])
        MetricsCollector.record_metric('system.memory.used', memory['used'])
        
        # Disk usage
        disk = SystemMonitor.get_disk_usage()
        MetricsCollector.record_metric('system.disk.usage', disk['percent'])
        MetricsCollector.record_metric('system.disk.free', disk['free'])
        
        # Database metrics
        db_status = SystemMonitor.get_database_status()
        if db_status['status'] == 'healthy':
            MetricsCollector.record_metric('database.query_time', db_status['query_time'])
            MetricsCollector.record_metric('database.size', db_status['size'])
            MetricsCollector.record_metric('database.connections', db_status['connections'])
        
        # Cache metrics
        cache_status = SystemMonitor.get_cache_status()
        if cache_status['status'] == 'healthy':
            MetricsCollector.record_metric('cache.status', 1)
        else:
            MetricsCollector.record_metric('cache.status', 0)
        
        # Application metrics
        from django.contrib.sessions.models import Session
        active_sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        ).count()
        MetricsCollector.record_metric('app.active_sessions', active_sessions)
        
        # Check for alerts
        check_system_alerts()
        
        return "Metrics collected successfully"
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return f"Error: {e}"


@shared_task
def check_system_alerts():
    """Check system metrics and send alerts if needed."""
    try:
        metrics = MetricsCollector.get_current_metrics()
        
        # High CPU usage
        cpu_usage = metrics.get('system.cpu.usage', 0)
        if cpu_usage > 90:
            AlertManager.send_alert(
                'high_cpu',
                f'CPU usage is critically high: {cpu_usage}%',
                severity='critical'
            )
        elif cpu_usage > 75:
            AlertManager.send_alert(
                'high_cpu',
                f'CPU usage is high: {cpu_usage}%',
                severity='warning'
            )
        
        # High memory usage
        memory_usage = metrics.get('system.memory.usage', 0)
        if memory_usage > 90:
            AlertManager.send_alert(
                'high_memory',
                f'Memory usage is critically high: {memory_usage}%',
                severity='critical'
            )
        elif memory_usage > 80:
            AlertManager.send_alert(
                'high_memory',
                f'Memory usage is high: {memory_usage}%',
                severity='warning'
            )
        
        # Low disk space
        disk_usage = metrics.get('system.disk.usage', 0)
        if disk_usage > 90:
            AlertManager.send_alert(
                'low_disk',
                f'Disk usage is critically high: {disk_usage}%',
                severity='critical'
            )
        elif disk_usage > 80:
            AlertManager.send_alert(
                'low_disk',
                f'Disk usage is high: {disk_usage}%',
                severity='warning'
            )
        
        # Database issues
        db_query_time = metrics.get('database.query_time', 0)
        if db_query_time > 1.0:  # 1 second
            AlertManager.send_alert(
                'slow_database',
                f'Database queries are slow: {db_query_time:.2f}s',
                severity='warning'
            )
        
        # Cache issues
        cache_status = metrics.get('cache.status', 1)
        if cache_status == 0:
            AlertManager.send_alert(
                'cache_down',
                'Cache service is not responding',
                severity='error'
            )
        
        return "Alerts checked successfully"
        
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        return f"Error: {e}"


@shared_task
def generate_daily_report():
    """Generate and send daily system report."""
    try:
        # Collect metrics for the last 24 hours
        end_time = timezone.now()
        start_time = end_time - timedelta(days=1)
        
        report_data = {
            'date': end_time.date().isoformat(),
            'metrics': {}
        }
        
        # Collect average metrics
        metric_names = [
            'system.cpu.usage',
            'system.memory.usage',
            'system.disk.usage',
            'database.query_time',
            'app.active_sessions'
        ]
        
        for metric_name in metric_names:
            values = MetricsCollector.get_metric(metric_name, start_time, end_time)
            if values:
                avg_value = sum(v['value'] for v in values) / len(values)
                max_value = max(v['value'] for v in values)
                min_value = min(v['value'] for v in values)
                
                report_data['metrics'][metric_name] = {
                    'average': avg_value,
                    'maximum': max_value,
                    'minimum': min_value,
                    'samples': len(values)
                }
        
        # Get alerts for the period
        alert_pattern = f"{AlertManager.ALERT_PREFIX}*"
        alert_keys = cache.keys(alert_pattern)
        alerts = []
        
        for key in alert_keys:
            alert = cache.get(key)
            if alert and start_time.isoformat() <= alert['timestamp'] <= end_time.isoformat():
                alerts.append(alert)
        
        report_data['alerts'] = alerts
        
        # Send report to admins
        admins = User.objects.filter(is_superuser=True, is_active=True)
        admin_emails = list(admins.values_list('email', flat=True))
        
        if admin_emails:
            subject = f"VivaCRM Daily Report - {report_data['date']}"
            message = format_daily_report(report_data)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True
            )
        
        # Store report
        report_key = f"report:daily:{report_data['date']}"
        cache.set(report_key, report_data, 30 * 24 * 60 * 60)  # Keep for 30 days
        
        return "Daily report generated and sent"
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return f"Error: {e}"


def format_daily_report(report_data):
    """Format daily report data as text."""
    report = f"""
VivaCRM Daily System Report
Date: {report_data['date']}

System Metrics (24-hour averages):
"""
    
    for metric_name, values in report_data['metrics'].items():
        report += f"\n{metric_name}:"
        report += f"\n  Average: {values['average']:.2f}"
        report += f"\n  Maximum: {values['maximum']:.2f}"
        report += f"\n  Minimum: {values['minimum']:.2f}"
        report += f"\n  Samples: {values['samples']}"
        report += "\n"
    
    if report_data['alerts']:
        report += "\n\nAlerts:\n"
        for alert in report_data['alerts']:
            report += f"\n[{alert['severity'].upper()}] {alert['type']}"
            report += f"\n  Time: {alert['timestamp']}"
            report += f"\n  Message: {alert['message']}"
            report += "\n"
    else:
        report += "\n\nNo alerts in the last 24 hours.\n"
    
    return report


# Monitoring views for dashboard
def get_monitoring_dashboard_data():
    """Get monitoring data for dashboard display."""
    current_metrics = MetricsCollector.get_current_metrics()
    
    # Get recent alerts
    alert_pattern = f"{AlertManager.ALERT_PREFIX}*"
    alert_keys = cache.keys(alert_pattern)[-10:]  # Last 10 alerts
    
    recent_alerts = []
    for key in alert_keys:
        alert = cache.get(key)
        if alert:
            recent_alerts.append(alert)
    
    # System status
    system_status = {
        'cpu': {
            'value': current_metrics.get('system.cpu.usage', 0),
            'status': 'ok' if current_metrics.get('system.cpu.usage', 0) < 75 else 'warning'
        },
        'memory': {
            'value': current_metrics.get('system.memory.usage', 0),
            'status': 'ok' if current_metrics.get('system.memory.usage', 0) < 80 else 'warning'
        },
        'disk': {
            'value': current_metrics.get('system.disk.usage', 0),
            'status': 'ok' if current_metrics.get('system.disk.usage', 0) < 80 else 'warning'
        },
        'database': {
            'value': current_metrics.get('database.query_time', 0),
            'status': 'ok' if current_metrics.get('database.query_time', 0) < 0.5 else 'warning'
        },
        'cache': {
            'value': current_metrics.get('cache.status', 1),
            'status': 'ok' if current_metrics.get('cache.status', 1) == 1 else 'error'
        }
    }
    
    return {
        'system_status': system_status,
        'current_metrics': current_metrics,
        'recent_alerts': sorted(recent_alerts, key=lambda x: x['timestamp'], reverse=True)
    }