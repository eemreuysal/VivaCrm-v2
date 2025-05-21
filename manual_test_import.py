#!/usr/bin/env python3
"""
Manual test the import directly in Django shell.
"""

import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from products.views_excel import ProductImportView
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

def manual_test():
    """Manually test the import view."""
    
    # Get user
    User = get_user_model()
    user = User.objects.get(email='test@example.com')
    
    # Create request factory
    factory = RequestFactory()
    
    # Read Excel file
    excel_file_path = '/Users/emreuysal/Downloads/urun_excel_sablonu.xlsx'
    with open(excel_file_path, 'rb') as f:
        excel_content = f.read()
    
    # Create uploaded file
    uploaded_file = SimpleUploadedFile(
        name='test_import.xlsx',
        content=excel_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Create POST request
    request = factory.post('/products/excel/import/', {
        'excel_file': uploaded_file,
        'update_existing': 'on'
    })
    
    # Add user to request
    request.user = user
    
    # Add messages middleware
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    # Create view instance and process request
    view = ProductImportView()
    
    try:
        response = view.post(request)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"Redirect to: {response.url}")
        else:
            # Check for errors in response
            content = response.content.decode('utf-8')
            print(f"Response length: {len(content)}")
            
            # Look for error messages
            if 'error' in content.lower():
                import re
                errors = re.findall(r'<div[^>]*class="[^"]*alert-error[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
                for error in errors:
                    clean_error = re.sub(r'<.*?>', '', error).strip()
                    print(f"Error: {clean_error}")
        
        # Check messages
        all_messages = list(messages)
        if all_messages:
            print("\nMessages:")
            for msg in all_messages:
                print(f"  {msg.level}: {msg}")
                
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    manual_test()