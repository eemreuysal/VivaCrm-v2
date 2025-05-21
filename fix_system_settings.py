#!/usr/bin/env python
"""
Fix duplicate SystemSettings entries.
This script removes duplicate SystemSettings and ensures only default settings remain.
"""
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from admin_panel.models import SystemSettings

def fix_duplicate_settings():
    """Remove duplicate SystemSettings entries and ensure default settings exist."""
    
    # Print current status
    print(f"Current SystemSettings count: {SystemSettings.objects.count()}")
    
    # Delete all existing settings
    SystemSettings.objects.all().delete()
    print("All SystemSettings have been deleted.")
    
    # Create default settings
    default_settings = [
        {'key': 'company_name', 'value': 'VivaCRM', 'category': 'general', 'description': 'Şirket adı'},
        {'key': 'company_short_name', 'value': 'Viva', 'category': 'general', 'description': 'Kısa şirket adı'},
        {'key': 'items_per_page', 'value': '25', 'category': 'general', 'description': 'Sayfa başına öğe sayısı'},
        {'key': 'default_currency', 'value': 'USD', 'category': 'general', 'description': 'Varsayılan para birimi'},
        {'key': 'date_format', 'value': 'd.m.Y', 'category': 'general', 'description': 'Tarih formatı'},
        {'key': 'time_format', 'value': 'H:i', 'category': 'general', 'description': 'Saat formatı'},
    ]
    
    for setting in default_settings:
        SystemSettings.objects.create(**setting)
        print(f"Created setting: {setting['key']} = {setting['value']}")
    
    print(f"\nSettings fixed! New count: {SystemSettings.objects.count()}")

if __name__ == "__main__":
    fix_duplicate_settings()