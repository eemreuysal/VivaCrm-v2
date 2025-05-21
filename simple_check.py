import os
import sys

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Add parent directory to sys.path if needed
sys.path.insert(0, os.path.abspath('.'))

# Try to import Django settings
print("Attempting to import settings...")
from django.conf import settings

print("\nChecking if critical apps are in INSTALLED_APPS:")
print("- Admin app:", 'django.contrib.admin' in settings.INSTALLED_APPS)
print("- Auth app:", 'django.contrib.auth' in settings.INSTALLED_APPS) 
print("- Sessions app:", 'django.contrib.sessions' in settings.INSTALLED_APPS)
print("- Django Prometheus:", 'django_prometheus' in settings.INSTALLED_APPS)

print("\nINSTALLED_APPS:")
for app in settings.INSTALLED_APPS:
    print(f"- {app}")

# Attempt to import the admin module
print("\nAttempting to import django.contrib.admin...")
try:
    import django.contrib.admin
    print("  Success!")
except Exception as e:
    print(f"  Error: {e}")

# Try Django setup
print("\nAttempting django.setup()...")
import django
try:
    django.setup()
    print("  Success!")
except Exception as e:
    print(f"  Error: {e}")

# Check app registry after setup
from django.apps import apps
print("\nApp registry after setup:")
try:
    admin_app = apps.get_app_config('admin')
    print(f"- Admin app: {admin_app}")
except LookupError as e:
    print(f"- Admin app error: {e}")