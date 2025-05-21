import os
import requests
from requests.auth import HTTPBasicAuth

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

# API URL'i
url = "http://localhost:8000/orders/import/"

# Dosyayı aç ve gönder
with open(excel_path, 'rb') as file:
    files = {
        'file': (os.path.basename(excel_path), file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    # Basic auth ile gönder
    auth = HTTPBasicAuth('admin', '1234')
    
    # Headers
    headers = {
        'Accept': 'application/json'
    }
    
    print("Sending request to:", url)
    response = requests.post(url, files=files, auth=auth, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content Type: {response.headers.get('content-type')}")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        print(f"Response JSON: {response.json()}")
    else:
        print(f"Response Text: {response.text[:500]}")