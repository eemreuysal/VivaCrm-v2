"""
Configuration for Celery scheduled tasks and beat scheduler.
This module defines periodic tasks and their schedules with performance optimizations.
"""
from celery.schedules import crontab
from datetime import timedelta
from django.conf import settings

# Task routing configuration with optimized queues
CELERY_TASK_ROUTES = {
    # High-priority tasks
    'products.tasks.check_low_stock_levels': {'queue': 'high'},
    'orders.tasks.send_order_reminder': {'queue': 'high'},
    'invoices.tasks.send_payment_reminder': {'queue': 'high'},
    
    # Excel import/export tasks
    'products.tasks.product_import': {'queue': 'excel_import'},
    'products.tasks.stock_adjustment': {'queue': 'excel_import'},
    'products.tasks.import_status': {'queue': 'excel_import'},
    'orders.tasks.order_import': {'queue': 'excel_import'},
    'orders.tasks.import_status': {'queue': 'excel_import'},
    
    # Excel export tasks
    'products.tasks.product_export': {'queue': 'excel_export'},
    'orders.tasks.order_export': {'queue': 'excel_export'},
    
    # Long-running tasks
    'reports.tasks.generate_sales_report': {'queue': 'reports'},
    'reports.tasks.generate_customer_activity_report': {'queue': 'reports'},
    'admin_panel.tasks.backup_database': {'queue': 'maintenance'},
    'admin_panel.tasks.backup_media_files': {'queue': 'maintenance'},
    
    # Default routing for other tasks
    'products.tasks.*': {'queue': 'default'},
    'orders.tasks.*': {'queue': 'default'},
    'dashboard.tasks.*': {'queue': 'default'},
    'admin_panel.tasks.*': {'queue': 'default'},
    'invoices.tasks.*': {'queue': 'default'},
    'reports.tasks.*': {'queue': 'default'},
    'accounts.tasks.*': {'queue': 'default'},
}

# Task time limits with realistic values
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes global limit
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit

# Specific task time limits for different task types
CELERY_TASK_ANNOTATIONS = {
    # Excel import tasks (can be large)
    'products.tasks.product_import': {
        'time_limit': 1800,  # 30 minutes
        'soft_time_limit': 1500,  # 25 minutes
        'rate_limit': '1/m',  # Max 1 per minute
    },
    'orders.tasks.order_import': {
        'time_limit': 1800,  # 30 minutes
        'soft_time_limit': 1500,  # 25 minutes
        'rate_limit': '1/m',
    },
    'products.tasks.stock_adjustment': {
        'time_limit': 900,  # 15 minutes
        'soft_time_limit': 780,  # 13 minutes
        'rate_limit': '2/m',
    },
    
    # Report generation tasks
    'reports.tasks.generate_sales_report': {
        'time_limit': 600,  # 10 minutes
        'soft_time_limit': 540,  # 9 minutes
        'rate_limit': '10/h',  # Max 10 per hour
    },
    
    # Backup tasks
    'admin_panel.tasks.backup_database': {
        'time_limit': 3600,  # 60 minutes
        'soft_time_limit': 3300,  # 55 minutes
        'rate_limit': '1/d',  # Max 1 per day
    },
}

# Queue configuration with concurrency control
CELERY_QUEUES = {
    'high': {
        'priority': 10,
        'max_concurrency': 4,
    },
    'default': {
        'priority': 5,
        'max_concurrency': 2,
    },
    'excel_import': {
        'priority': 8,
        'max_concurrency': 1,  # Prevent overwhelming the system
    },
    'excel_export': {
        'priority': 7,
        'max_concurrency': 2,
    },
    'reports': {
        'priority': 3,
        'max_concurrency': 1,
    },
    'maintenance': {
        'priority': 1,
        'max_concurrency': 1,
    },
}

# Optimize worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Reduce memory usage
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart workers periodically
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True

# Result backend optimization
CELERY_RESULT_BACKEND_MAX_RETRIES = 10
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_CACHE_BACKEND = 'default'
CELERY_CACHE_KEY_PREFIX = 'celery-meta-'

# Beat schedule optimization
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE_FILENAME = 'celerybeat-schedule'

# Define periodic tasks and their schedules with optimized timing
CELERY_BEAT_SCHEDULE = {
    # Critical daily tasks (run during low-traffic hours)
    'daily-check-low-stock': {
        'task': 'products.tasks.check_low_stock_levels',
        'schedule': crontab(hour=2, minute=0),  # 02:00 AM
        'options': {
            'expires': 3600,
            'priority': 10,
        }
    },
    'daily-expire-promotions': {
        'task': 'products.tasks.expire_product_promotions',
        'schedule': crontab(hour=2, minute=30),  # 02:30 AM
        'options': {
            'expires': 3600,
            'priority': 8,
        }
    },
    
    # Order management tasks
    'daily-send-order-reminders': {
        'task': 'orders.tasks.send_order_reminder',
        'schedule': crontab(hour=9, minute=0),  # 09:00 AM
        'options': {
            'expires': 3600,
            'priority': 9,
        },
        'kwargs': {'days': 3}
    },
    'twice-daily-cancel-abandoned-orders': {
        'task': 'orders.tasks.cancel_abandoned_orders',
        'schedule': crontab(hour='2,14', minute=0),  # 02:00 AM and 02:00 PM
        'options': {
            'expires': 3600,
            'priority': 5,
        },
        'kwargs': {'days': 7}
    },
    'daily-order-summary': {
        'task': 'orders.tasks.generate_daily_order_summary',
        'schedule': crontab(hour=23, minute=55),  # 11:55 PM
        'options': {
            'expires': 600,
            'priority': 7,
        }
    },
    
    # Invoice tasks
    'daily-payment-reminders': {
        'task': 'invoices.tasks.send_payment_reminder',
        'schedule': crontab(hour=10, minute=0),  # 10:00 AM
        'options': {
            'expires': 3600,
            'priority': 8,
        },
        'kwargs': {'days': 7}
    },
    'hourly-generate-invoices': {
        'task': 'invoices.tasks.bulk_generate_invoices_for_completed_orders',
        'schedule': crontab(minute=0),  # Every hour
        'options': {
            'expires': 1800,
            'priority': 6,
        }
    },
    
    # Weekly maintenance tasks
    'weekly-database-backup': {
        'task': 'admin_panel.tasks.backup_database',
        'schedule': crontab(day_of_week=0, hour=1, minute=0),  # Sunday 01:00 AM
        'options': {
            'expires': 7200,
            'priority': 2,
        }
    },
    'weekly-media-backup': {
        'task': 'admin_panel.tasks.backup_media_files',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 02:00 AM
        'options': {
            'expires': 7200,
            'priority': 2,
        }
    },
    'weekly-report-cleanup': {
        'task': 'products.tasks.cleanup_old_reports',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 03:00 AM
        'options': {
            'expires': 3600,
            'priority': 3,
        }
    },
    'weekly-update-sales-stats': {
        'task': 'orders.tasks.update_product_sales_stats',
        'schedule': crontab(day_of_week=1, hour=3, minute=0),  # Monday 03:00 AM
        'options': {
            'expires': 3600,
            'priority': 4,
        }
    },
    
    # Monthly tasks
    'monthly-comprehensive-report': {
        'task': 'reports.tasks.generate_sales_report',
        'schedule': crontab(day_of_month=1, hour=4, minute=0),  # 1st day 04:00 AM
        'options': {
            'expires': 10800,
            'priority': 3,
        }
    },
    'monthly-stock-report': {
        'task': 'products.tasks.generate_stock_movements_report',
        'schedule': crontab(day_of_month=1, hour=5, minute=0),  # 1st day 05:00 AM
        'options': {
            'expires': 7200,
            'priority': 3,
        }
    },
    
    # System monitoring
    'hourly-error-check': {
        'task': 'admin_panel.tasks.notify_admins_of_system_errors',
        'schedule': crontab(minute=30),  # Every hour at :30
        'options': {
            'expires': 1800,
            'priority': 9,
        }
    },
    
    # Performance monitoring
    'collect-system-metrics': {
        'task': 'core.monitoring.collect_system_metrics',
        'schedule': timedelta(minutes=5),  # Every 5 minutes
        'options': {
            'expires': 300,
            'priority': 8,
        }
    },
    'check-system-alerts': {
        'task': 'core.monitoring.check_system_alerts',
        'schedule': timedelta(minutes=10),  # Every 10 minutes
        'options': {
            'expires': 600,
            'priority': 9,
        }
    },
    'daily-monitoring-report': {
        'task': 'core.monitoring.generate_daily_report',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
        'options': {
            'expires': 3600,
            'priority': 5,
        }
    },
    
    # Dashboard performance and caching
    'hourly-dashboard-refresh': {
        'task': 'dashboard.tasks.refresh_dashboard_data',
        'schedule': crontab(minute=15),  # Every hour at :15
        'options': {
            'expires': 3000,
            'priority': 8,  # Daha yüksek öncelik
        }
    },
    'daily-dashboard-cache-cleanup': {
        'task': 'dashboard.tasks.clean_old_dashboard_caches',
        'schedule': crontab(hour=1, minute=30),  # Daily at 1:30 AM
        'options': {
            'expires': 3600,
            'priority': 5,  # Orta öncelik
        }
    },
    'daily-dashboard-cache-generation': {
        'task': 'dashboard.tasks.generate_dashboard_cache_data',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3:00 AM
        'options': {
            'expires': 3600,
            'priority': 7,  # Önemli ama kritik olmayan görev
        }
    },
    'periodic-dashboard-performance-monitoring': {
        'task': 'dashboard.tasks.monitor_dashboard_performance',
        'schedule': crontab(hour='*/4', minute=45),  # Every 4 hours at :45
        'options': {
            'expires': 1800,
            'priority': 6,  # İzleme orta öncelikli
        }
    },
}

# Celery optimization settings
CELERY_OPTIMIZATION_SETTINGS = {
    # Task execution
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_ignore_result': False,
    
    # Connection pooling
    'broker_pool_limit': 10,
    'redis_socket_keepalive': True,
    'redis_socket_keepalive_options': {
        'TCP_KEEPIDLE': 60,
        'TCP_KEEPINTVL': 30,
        'TCP_KEEPCNT': 3,
    },
    
    # Task result caching
    'result_cache_max': 1000,
    'result_persistent': True,
    
    # Error handling
    'task_default_retry_delay': 60,
    'task_max_retries': 3,
}

# Apply optimization settings
for key, value in CELERY_OPTIMIZATION_SETTINGS.items():
    globals()[f'CELERY_{key.upper()}'] = value

# Performance monitoring
if getattr(settings, 'DEBUG', False):
    CELERY_SEND_TASK_EVENTS = True
    CELERY_SEND_EVENTS = True