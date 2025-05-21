#!/usr/bin/env python3
"""
Test the import view directly with a sample file.
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
from products.models import Product, Category
import uuid

def test_import_view():
    """Test the import view with an actual Excel file."""
    
    # Get or create a test user with unique email
    User = get_user_model()
    
    # Use existing user or create new one
    try:
        user = User.objects.get(email='test@example.com')
        username = user.username
    except User.DoesNotExist:
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(
            username=username,
            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass'
        )
    
    # Create a test client and login
    client = Client()
    logged_in = client.login(username=username, password='testpass')
    
    # If login failed, try with the existing user
    if not logged_in:
        # Get the existing user and set password
        user = User.objects.get(email='test@example.com')
        user.set_password('testpass')
        user.save()
        logged_in = client.login(username=user.username, password='testpass')
    
    print(f"Login successful: {logged_in}")
    print(f"Using user: {user.username}")
    
    # Read the Excel file
    excel_file_path = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
    
    # Check if file exists
    if not os.path.exists(excel_file_path):
        print(f"Error: Excel file not found at {excel_file_path}")
        return
    
    with open(excel_file_path, 'rb') as f:
        excel_content = f.read()
    
    print(f"Excel file size: {len(excel_content)} bytes")
    
    # Create uploaded file
    uploaded_file = SimpleUploadedFile(
        name='test_import.xlsx',
        content=excel_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Get initial counts
    initial_product_count = Product.objects.count()
    initial_category_count = Category.objects.count()
    
    print(f"Initial products: {initial_product_count}")
    print(f"Initial categories: {initial_category_count}")
    
    # Test the import view
    print("\nSending POST request to import view...")
    response = client.post('/products/excel/import/', {
        'excel_file': uploaded_file,
        'update_existing': 'on'  # Update existing products
    }, follow=True)  # Follow redirects
    
    print(f"\nResponse status: {response.status_code}")
    
    # Print response content for debugging
    content = response.content.decode('utf-8')
    
    # Check for error messages
    if 'error' in content.lower() or 'hata' in content.lower():
        # Find and print error messages
        import re
        errors = re.findall(r'<div[^>]*class="[^"]*alert[^"]*error[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
        for error in errors:
            clean_error = re.sub(r'<.*?>', '', error).strip()
            print(f"\nError: {clean_error}")
    
    # Check for success messages
    if 'success' in content.lower() or 'başarı' in content.lower():
        import re
        successes = re.findall(r'<div[^>]*class="[^"]*alert[^"]*success[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
        for success in successes:
            clean_success = re.sub(r'<.*?>', '', success).strip()
            print(f"\nSuccess: {clean_success}")
    
    # Check final counts
    final_product_count = Product.objects.count()
    final_category_count = Category.objects.count()
    
    print(f"\nFinal products: {final_product_count}")
    print(f"Final categories: {final_category_count}")
    print(f"Products added/updated: {final_product_count - initial_product_count}")
    print(f"Categories created: {final_category_count - initial_category_count}")
    
    # Check for logged messages
    from django.contrib.messages import get_messages
    messages = list(get_messages(response.wsgi_request))
    if messages:
        print("\nMessages:")
        for message in messages:
            print(f"  {message.tags}: {message}")
    
    # If no messages or errors, check if we're on the product list page
    if response.status_code == 200 and '/products/' in response.request['PATH_INFO']:
        print("\nSuccessfully redirected to product list page")


if __name__ == '__main__':
    test_import_view()