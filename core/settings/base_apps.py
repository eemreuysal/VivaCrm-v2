"""Store the original INSTALLED_APPS to use in other settings files"""

# Original INSTALLED_APPS from base.py
BASE_INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    
    # Third party apps
    "rest_framework",
    "drf_spectacular",
    "debug_toolbar",
    "django_extensions",
    "crispy_forms",
    "crispy_tailwind",
    "django_filters",
    "django_celery_results",
    "django_celery_beat",
    "django_vite",
    
    # Project apps
    "core.apps.CoreConfig",  # Core app with signals
    "accounts",
    "dashboard",
    "customers",
    "products",
    "orders",
    "reports",
    "invoices",
    "admin_panel",
]