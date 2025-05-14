from django.contrib.auth import get_user_model
from django.core.management import call_command
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

# Kullanıcı bilgileri
username = 'emreuysal'
email = 'emre@vivacrm.com'
password = 'emre1234'
first_name = 'Emre'
last_name = 'Uysal'

# Eğer aynı kullanıcı adıyla kullanıcı varsa, silelim (isteğe bağlı)
if User.objects.filter(username=username).exists():
    User.objects.filter(username=username).delete()
    print(f'Existing user with username {username} was deleted.')

# Yeni superuser oluştur
User.objects.create_superuser(
    username=username,
    email=email,
    password=password,
    first_name=first_name,
    last_name=last_name
)
print(f'Superuser {username} created successfully!')
print(f'Email: {email}')
print(f'Password: {password}')
print(f'You can login at http://127.0.0.1:8000/admin/ or through the main application login page.')