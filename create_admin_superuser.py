"""
Create a new superuser account with username as the primary login field.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if the superuser with this username already exists
if not User.objects.filter(username="admin").exists():
    # Create a new superuser
    User.objects.create_superuser(
        username="admin",
        email="admin@vivacrm.com",
        password="admin123456",
        first_name="Admin",
        last_name="User"
    )
    print("Superuser 'admin' created successfully.")
else:
    # Update the existing superuser's password
    user = User.objects.get(username="admin")
    user.set_password("admin123456")
    user.save()
    print("Superuser 'admin' password updated successfully.")