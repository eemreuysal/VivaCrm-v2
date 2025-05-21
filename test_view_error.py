#!/usr/bin/env python3
"""
Test the view to see exact error message.
"""

import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_view_error():
    """Test the view to see the exact error."""
    
    # Get or create a test user
    User = get_user_model()
    user = User.objects.get(email='test@example.com')
    
    # Create a test client and login
    client = Client()
    user.set_password('testpass')
    user.save()
    logged_in = client.login(username=user.username, password='testpass')
    print(f"Login successful: {logged_in}")
    
    # Read the Excel file
    excel_file_path = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
    with open(excel_file_path, 'rb') as f:
        excel_content = f.read()
    
    # Create uploaded file
    uploaded_file = SimpleUploadedFile(
        name='test_import.xlsx',
        content=excel_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Test the import view WITHOUT following redirects
    response = client.post('/products/excel/import/', {
        'excel_file': uploaded_file,
        'update_existing': 'on'
    }, follow=False)
    
    print(f"Response status: {response.status_code}")
    
    # If it's a 400 error, print the content
    if response.status_code == 400:
        print("\nResponse content:")
        content = response.content.decode('utf-8')
        
        # Look for specific error patterns
        import re
        
        # Django form errors
        form_errors = re.findall(r'<ul[^>]*class="errorlist[^"]*"[^>]*>(.*?)</ul>', content, re.DOTALL)
        if form_errors:
            print("\nForm errors found:")
            for error_list in form_errors:
                errors = re.findall(r'<li>(.*?)</li>', error_list)
                for error in errors:
                    print(f"  - {error}")
        
        # Check for exception details
        if 'Exception Value:' in content:
            exc_value = re.search(r'Exception Value:.*?<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
            if exc_value:
                print(f"\nException Value: {exc_value.group(1).strip()}")
        
        # Check for traceback
        if 'Traceback' in content:
            traceback = re.search(r'<div[^>]*id="traceback"[^>]*>(.*?)</div>', content, re.DOTALL)
            if traceback:
                print("\nTraceback found in response")
                # Print first few lines
                lines = traceback.group(1).split('\n')[:10]
                for line in lines:
                    print(line.strip())
        
        # If no specific error found, print beginning of content
        if not form_errors and 'Exception' not in content:
            print("\nFirst 1000 characters of response:")
            print(content[:1000])
    
    elif response.status_code == 302:
        print(f"Redirect to: {response.url}")
    
    elif response.status_code == 200:
        print("Response OK - checking content...")
        content = response.content.decode('utf-8')
        # Check for error messages in the HTML
        if 'error' in content.lower() or 'hata' in content.lower():
            import re
            errors = re.findall(r'<div[^>]*class="[^"]*alert-error[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
            for error in errors:
                clean_error = re.sub(r'<.*?>', '', error).strip()
                print(f"Error message: {clean_error}")


if __name__ == '__main__':
    test_view_error()