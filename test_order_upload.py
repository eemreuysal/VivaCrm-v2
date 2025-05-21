#!/usr/bin/env python
"""
Test order upload directly
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from accounts.models import User
import pandas as pd
from io import BytesIO

# Create test user
try:
    user = User.objects.create_user('test_user', 'test@example.com', 'testpass123')
except:
    user = User.objects.get(username='test_user')

# Create client and login
client = Client()
client.login(username='test_user', password='testpass123')

# Create test Excel file
df = pd.DataFrame({
    'customer_email': ['test@example.com'],
    'product_sku': ['TEST-001'],
    'quantity': [1]
})

# Convert to Excel
excel_file = BytesIO()
df.to_excel(excel_file, index=False)
excel_file.seek(0)
excel_file.name = 'test_orders.xlsx'  # File name is needed

# Make the request
from django.core.files.uploadedfile import SimpleUploadedFile
upload_file = SimpleUploadedFile('test_orders.xlsx', excel_file.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

response = client.post('/orders/import/', {
    'excel_file': upload_file,
    'update_existing': 'off'
}, format='multipart', HTTP_HOST='127.0.0.1:8000', HTTP_X_REQUESTED_WITH='XMLHttpRequest')

print(f"Status: {response.status_code}")
print(f"Content: {response.content.decode('utf-8')[:500]}")
if response.status_code == 400:
    print("Error occured")
    if hasattr(response, 'json'):
        import json
        try:
            data = json.loads(response.content)
            print(f"JSON Response: {data}")
        except:
            print("Could not parse JSON")