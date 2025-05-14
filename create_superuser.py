from django.contrib.auth import get_user_model
from django.core.management import call_command
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@vivacrm.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')