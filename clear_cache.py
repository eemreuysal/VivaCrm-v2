"""
Script to clear all Django caches.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.core.cache import cache

# Clear all caches
cache.clear()

print("All caches have been cleared successfully.")