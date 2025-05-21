#!/usr/bin/env python3
"""
Test the view with proper host configuration.
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

def test_view_with_host():
    """Test the view with proper host."""
    
    # Get or create a test user
    User = get_user_model()
    user = User.objects.get(email='test@example.com')
    
    # Create a test client and login
    client = Client(HTTP_HOST='localhost')
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
    
    # Test the import view
    response = client.post('/products/excel/import/', {
        'excel_file': uploaded_file,
        'update_existing': 'on'
    }, follow=True)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check for messages
        import re
        
        # Success messages
        success_messages = re.findall(r'<div[^>]*class="[^"]*alert-success[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
        for msg in success_messages:
            clean_msg = re.sub(r'<.*?>', '', msg).strip()
            print(f"Success: {clean_msg}")
        
        # Error messages
        error_messages = re.findall(r'<div[^>]*class="[^"]*alert-error[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
        for msg in error_messages:
            clean_msg = re.sub(r'<.*?>', '', msg).strip()
            print(f"Error: {clean_msg}")
        
        # Info messages
        info_messages = re.findall(r'<div[^>]*class="[^"]*alert-info[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
        for msg in info_messages:
            clean_msg = re.sub(r'<.*?>', '', msg).strip()
            print(f"Info: {clean_msg}")
        
        # Check if we're on the product list page
        if '/products/' in response.request['PATH_INFO']:
            print("\nSuccessfully redirected to product list page")
        
        # Also check for Django messages
        from django.contrib.messages import get_messages
        messages = list(get_messages(response.wsgi_request))
        if messages:
            print("\nDjango Messages:")
            for message in messages:
                print(f"  {message.tags}: {message}")


if __name__ == '__main__':
    test_view_with_host()