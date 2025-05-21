"""Test regular web upload path (not API)"""
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

# Login
login_url = "http://localhost:8000/accounts/login/"
response = session.get(login_url)

# Extract CSRF token
import re
csrf_token = None
if 'csrfmiddlewaretoken' in response.text:
    match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
    if match:
        csrf_token = match.group(1)

# Login
login_data = {
    'username': 'admin',
    'password': '1234',
    'csrfmiddlewaretoken': csrf_token
}

print("Logging in...")
response = session.post(login_url, data=login_data)
print(f"Login status: {response.status_code}")

# Web page
web_url = "http://localhost:8000/orders/import/"

# Get page to get new CSRF token
response = session.get(web_url)
if 'csrfmiddlewaretoken' in response.text:
    match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
    if match:
        csrf_token = match.group(1)

# Upload file
with open(excel_path, 'rb') as file:
    files = {
        'excel_file': (os.path.basename(excel_path), file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    data = {
        'csrfmiddlewaretoken': csrf_token
    }
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/html, */*',
        'Referer': web_url
    }
    
    print("Uploading to regular web endpoint...")
    response = session.post(web_url, files=files, data=data, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        print(f"Response JSON: {response.json()}")
    else:
        print(f"Response Text: {response.text[:500]}")