"""
Configuration for Celery scheduled tasks and beat scheduler.
This module defines periodic tasks and their schedules.
"""
from celery.schedules import crontab
from datetime import timedelta

# Define periodic tasks and their schedules
CELERY_BEAT_SCHEDULE = {
    # Daily tasks
    'daily-dashboard-cache': {
        'task': 'dashboard.tasks.generate_dashboard_cache_data',
        'schedule': crontab(hour=0, minute=5),  # Every day at 00:05
        'options': {'expires': 3600}
    },
    'daily-system-status-report': {
        'task': 'dashboard.tasks.daily_system_status_report',
        'schedule': crontab(hour=0, minute=15),  # Every day at 00:15
        'options': {'expires': 3600}
    },
    'daily-check-low-stock': {
        'task': 'products.tasks.check_low_stock_levels',
        'schedule': crontab(hour=8, minute=0),  # Every day at 08:00
        'options': {'expires': 3600}
    },
    'daily-send-payment-reminders': {
        'task': 'invoices.tasks.send_payment_reminder',
        'schedule': crontab(hour=9, minute=0),  # Every day at 09:00
        'options': {'expires': 3600},
        'kwargs': {'days': 7}  # Reminders for invoices 7 days past due
    },
    'daily-expire-product-promotions': {
        'task': 'products.tasks.expire_product_promotions',
        'schedule': crontab(hour=0, minute=30),  # Every day at 00:30
        'options': {'expires': 3600}
    },
    
    # Weekly tasks
    'weekly-database-backup': {
        'task': 'admin_panel.tasks.backup_database',
        'schedule': crontab(day_of_week=0, hour=1, minute=0),  # Every Sunday at 01:00
        'options': {'expires': 7200}
    },
    'weekly-media-backup': {
        'task': 'admin_panel.tasks.backup_media_files',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Every Sunday at 02:00
        'options': {'expires': 7200}
    },
    'weekly-clean-old-files': {
        'task': 'admin_panel.tasks.clean_old_files',
        'schedule': crontab(day_of_week=6, hour=3, minute=0),  # Every Saturday at 03:00
        'options': {'expires': 7200}
    },
    'weekly-sales-report': {
        'task': 'reports.tasks.generate_sales_report',
        'schedule': crontab(day_of_week=1, hour=5, minute=0),  # Every Monday at 05:00
        'options': {'expires': 7200}
    },
    'weekly-email-reports': {
        'task': 'reports.tasks.send_scheduled_reports_to_users',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Every Monday at 08:00
        'options': {'expires': 7200}
    },
    'weekly-customer-activity-report': {
        'task': 'reports.tasks.generate_customer_activity_report',
        'schedule': crontab(day_of_week=1, hour=6, minute=0),  # Every Monday at 06:00
        'options': {'expires': 7200},
        'kwargs': {'days': 7}  # Last week's activity
    },
    
    # Monthly tasks
    'monthly-inactive-user-notification': {
        'task': 'accounts.tasks.send_inactive_user_notification',
        'schedule': crontab(day_of_month=1, hour=10, minute=0),  # 1st day of month at 10:00
        'options': {'expires': 10800},
        'kwargs': {'days': 30}  # Users inactive for 30 days
    },
    'monthly-stock-movements-report': {
        'task': 'products.tasks.generate_stock_movements_report',
        'schedule': crontab(day_of_month=1, hour=4, minute=0),  # 1st day of month at 04:00
        'options': {'expires': 10800}
    },
    'monthly-update-product-sales-stats': {
        'task': 'orders.tasks.update_product_sales_stats',
        'schedule': crontab(day_of_month='1', hour=3, minute=0),  # 1st day of month at 03:00
        'options': {'expires': 10800}
    },
    
    # Hourly tasks
    'hourly-error-check': {
        'task': 'admin_panel.tasks.notify_admins_of_system_errors',
        'schedule': crontab(minute=0),  # Every hour at XX:00
        'options': {'expires': 3600}
    },
    
    # More frequent tasks
    'generate-invoices-for-completed-orders': {
        'task': 'invoices.tasks.bulk_generate_invoices_for_completed_orders',
        'schedule': timedelta(minutes=30),  # Every 30 minutes
        'options': {'expires': 1800}
    },
    'cancel-abandoned-orders': {
        'task': 'orders.tasks.cancel_abandoned_orders',
        'schedule': timedelta(hours=12),  # Twice per day
        'options': {'expires': 3600},
        'kwargs': {'days': 7}  # Cancel orders abandoned for 7 days
    },
}