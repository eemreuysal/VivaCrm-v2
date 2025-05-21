import os
import sys
import importlib

# Set environment variable to use development settings
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"

# Try direct import of the settings module
print("Attempting direct import of core.settings...")
try:
    import core.settings
    print("Import successful")
except Exception as e:
    print(f"Import error: {e}")

# Try to import each settings file individually
print("\nAttempting individual imports...")

settings_modules = [
    "core.settings.base",
    "core.settings.base_apps",
    "core.settings.development",
    "core.settings.production",
    "core.settings.vite"
]

for module_name in settings_modules:
    try:
        print(f"Importing {module_name}...")
        module = importlib.import_module(module_name)
        print(f"  - Success")
        
        # Try to print INSTALLED_APPS if it exists
        if hasattr(module, "INSTALLED_APPS"):
            print(f"  - INSTALLED_APPS count: {len(module.INSTALLED_APPS)}")
            print(f"  - First few apps: {module.INSTALLED_APPS[:3]}")
    except Exception as e:
        print(f"  - Error: {e}")

# Print sys.path
print("\nPython path:")
for path in sys.path:
    print(f" - {path}")