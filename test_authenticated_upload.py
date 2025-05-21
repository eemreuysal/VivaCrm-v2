import requests
from bs4 import BeautifulSoup

# Start a session to handle cookies
session = requests.Session()

# First login
login_url = 'http://127.0.0.1:8000/accounts/login/'
response = session.get(login_url)
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

# Login with test credentials
login_data = {
    'csrfmiddlewaretoken': csrf_token,
    'username': 'admin',  
    'password': 'admin123'  
}

response = session.post(login_url, data=login_data)
print(f"Login response: {response.status_code}")

# Now try the upload
response = session.get('http://127.0.0.1:8000/orders/import/')
soup = BeautifulSoup(response.text, 'html.parser')
csrf_element = soup.find('input', {'name': 'csrfmiddlewaretoken'})

if csrf_element:
    csrf_token = csrf_element['value']
    print(f"CSRF Token: {csrf_token}")
    
    # Prepare the file
    files = {
        'excel_file': ('test_excel_file.xlsx', open('test_excel_file.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    data = {
        'csrfmiddlewaretoken': csrf_token,
        'update_existing': 'off'
    }
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # Make the POST request
    response = session.post('http://127.0.0.1:8000/orders/import/', files=files, data=data, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response Text: {response.text[:500]}")
    
    if response.status_code == 400:
        print("\nFull Response:")
        print(response.text)
else:
    print("Could not find CSRF token, page content:")
    print(response.text[:500])