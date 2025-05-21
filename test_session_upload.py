import os
import requests

# Test dosyası oluştur
excel_path = "/Users/emreuysal/Documents/Project/VivaCrm v2/test_orders.xlsx"
if not os.path.exists(excel_path):
    import pandas as pd
    data = {
        'customer_email': ['test1@example.com'],
        'product_sku': ['TEST001'],
        'quantity': [5],
        'unit_price': [150.00]
    }
    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)

# Session kullan
session = requests.Session()

# Login URL
login_url = "http://localhost:8000/accounts/login/"

# CSRF token al
print("Getting CSRF token...")
response = session.get(login_url)
csrf_token = None

# CSRF token'ı metin içinde ara
if 'csrfmiddlewaretoken' in response.text:
    import re
    match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
    if match:
        csrf_token = match.group(1)
        print(f"CSRF token: {csrf_token}")

# Login ol
login_data = {
    'username': 'admin',
    'password': '1234',
    'csrfmiddlewaretoken': csrf_token
}

print("Logging in...")
response = session.post(login_url, data=login_data)
print(f"Login response status: {response.status_code}")

# API URL'i
url = "http://localhost:8000/orders/import/"

# CSRF token yenile
print("Getting new CSRF token for upload...")
response = session.get(url)
if 'csrfmiddlewaretoken' in response.text:
    match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
    if match:
        csrf_token = match.group(1)
        print(f"New CSRF token: {csrf_token}")

# Dosyayı aç ve gönder
with open(excel_path, 'rb') as file:
    files = {
        'file': (os.path.basename(excel_path), file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    data = {
        'csrfmiddlewaretoken': csrf_token
    }
    
    # Headers
    headers = {
        'Accept': 'application/json, text/html, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': url
    }
    
    print("Sending upload request...")
    response = session.post(url, files=files, data=data, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content Type: {response.headers.get('content-type')}")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        print(f"Response JSON: {response.json()}")
    else:
        print(f"Response Text: {response.text[:500]}")