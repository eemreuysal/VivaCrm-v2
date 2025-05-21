#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User

# Create admin user
try:
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@vivacrm.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("Admin user created successfully!")
except Exception as e:
    print(f"Error: {e}")
    # Try to get existing admin
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.save()
    print("Admin password updated!")