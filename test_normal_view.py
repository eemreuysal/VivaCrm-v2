import os
import requests

# Test dosyası
excel_path = "/Users/emreuysal/Documents/Project/VivaCrm v2/test_order_import.xlsx"

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

# Normal URL
url = "http://localhost:8000/orders/import/"

# Get page to get fresh CSRF token
response = session.get(url)
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
        'Accept': 'application/json'
    }
    
    print("Uploading test file to normal view...")
    response = session.post(url, files=files, data=data, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Created: {data.get('created_count')}")
        print(f"Errors: {data.get('error_count')}")
        if data.get('errors'):
            print("First 5 errors:")
            for error in data['errors'][:5]:
                print(f"  - {error}")