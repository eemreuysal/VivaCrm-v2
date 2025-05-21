import os
import sys
import inspect

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Import Django settings
print("Importing Django settings...")
from django.conf import settings
from importlib import import_module

# Try to find the settings module file that's being used
print("\nTrying to find settings module...")
try:
    settings_module = import_module(os.environ["DJANGO_SETTINGS_MODULE"])
    file_path = inspect.getfile(settings_module)
    print(f"Settings module file: {file_path}")
except Exception as e:
    print(f"Error finding settings module: {e}")

# Check for INSTALLED_APPS in various modules
modules_to_check = [
    "core.settings",
    "core.settings.base",
    "core.settings.development",
    "core.settings.vite",
    "core.settings.base_apps",
]

print("\nInspecting various settings modules for INSTALLED_APPS:")
for module_name in modules_to_check:
    try:
        module = import_module(module_name)
        if hasattr(module, "INSTALLED_APPS"):
            apps = getattr(module, "INSTALLED_APPS")
            print(f"{module_name}: {len(apps)} apps, first few: {apps[:3]}")
        else:
            print(f"{module_name}: No INSTALLED_APPS attribute")
    except Exception as e:
        print(f"{module_name}: Error - {e}")

# Print the effective INSTALLED_APPS
print("\nEffective INSTALLED_APPS from settings object:")
for app in settings.INSTALLED_APPS:
    print(f"- {app}")

# Try to trace the settings loading process
print("\nTracking settings loading process...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try importing the individual settings files in order
import core.settings as settings_root_module
for attr in dir(settings_root_module):
    if attr.startswith("__"):
        continue
    value = getattr(settings_root_module, attr)
    if isinstance(value, list) and attr == "INSTALLED_APPS":
        print(f"Found INSTALLED_APPS in settings_root_module with {len(value)} items: {value[:3]}...")