#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from accounts.models import User

# Create a test client
client = Client()

# Login as admin
admin = User.objects.get(username='admin')
client.force_login(admin)

# Create a minimal Excel file
import pandas as pd
from io import BytesIO

# Create simple data
df = pd.DataFrame({
    'customer_email': ['test1@example.com'],
    'product_sku': ['TESTSKU'],
    'quantity': [1]
})

# Convert to Excel
excel_buffer = BytesIO()
df.to_excel(excel_buffer, index=False)
excel_buffer.seek(0)

# Create form data
from django.core.files.uploadedfile import SimpleUploadedFile

excel_file = SimpleUploadedFile(
    'test_orders.xlsx',
    excel_buffer.getvalue(),
    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# Make the request with debug
import logging
logging.basicConfig(level=logging.DEBUG)

response = client.post('/orders/import/', {
    'excel_file': excel_file,
    'update_existing': 'off'
}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Response: {response.content.decode('utf-8')}")

# Check if it's JSON
if response.headers.get('content-type') == 'application/json':
    import json
    data = json.loads(response.content)
    print(f"JSON Data: {data}")
else:
    print("Not JSON response")