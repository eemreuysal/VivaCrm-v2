import os
import sys
import importlib

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Try to import Django modules
print("Attempting to import Django...")
import django
print(f"Django version: {django.__version__}")

# Try to setup Django
print("\nAttempting to set up Django...")
django.setup()

# Check installed apps
from django.apps import apps
print("\nChecking installed apps:")
try:
    admin_app = apps.get_app_config("admin")
    print(f"Admin app: {admin_app}")
except LookupError as e:
    print(f"Admin app error: {e}")

# Check all installed apps
print("\nAll installed apps:")
for app_config in apps.get_app_configs():
    print(f" - {app_config.label}: {app_config.name}")

# Check INSTALLED_APPS setting
print("\nINSTALLED_APPS setting:")
from django.conf import settings
for app in settings.INSTALLED_APPS:
    print(f" - {app}")

# Check middleware
print("\nMIDDLEWARE setting:")
for middleware in settings.MIDDLEWARE:
    print(f" - {middleware}")