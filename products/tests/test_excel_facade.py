"""
Excel Facade pattern testleri.
"""
import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage

from ..models import Product, Category
from ..views.excel_facade import ExcelImportFacade, ExcelExportFacade
from ..forms import ExcelImportForm

User = get_user_model()


class ExcelFacadeTestCase(TestCase):
    """Excel Facade testleri"""
    
    def setUp(self):
        """Test setup"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        # Test kategorisi oluştur
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Test ürünü oluştur
        self.product = Product.objects.create(
            name='Test Product',
            code='TST001',
            price=100.00,
            category=self.category,
            sku='TST001-SKU',
            current_stock=10
        )
        
        # Test Excel dosyası oluştur
        self.excel_content = b'dummy content'  # Gerçek bir Excel dosyası olmalı
        self.excel_file = SimpleUploadedFile(
            "test.xlsx",
            self.excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Mock request oluştur
        self.request = self.factory.get('/')
        self.request.user = self.user
        
        # Django messages setup
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)
    
    @patch('products.views.excel_facade.ProductExcelManager')
    def test_excel_import_facade(self, mock_manager_class):
        """Import facade testi"""
        # Mock excel manager
        mock_manager = mock_manager_class.return_value
        mock_manager.import_products.return_value = {
            'total_rows': 10,
            'success_count': 8,
            'error_count': 2,
            'successes': [],
            'errors': [],
            'warnings': []
        }
        
        # Excel Facade
        facade = ExcelImportFacade(self.request)
        
        # Form oluştur ve validate et
        form_data = {'use_chunks': True, 'skip_validation': False}
        form_files = {'excel_file': self.excel_file}
        form = ExcelImportForm(form_data, form_files)
        
        self.assertTrue(form.is_valid())
        
        # Import işlemini test et (tempfile patch ile)
        with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
            # Mock geçici dosya
            mock_tmp = MagicMock()
            mock_tmp.name = '/tmp/test.xlsx'
            mock_tempfile.return_value.__enter__.return_value = mock_tmp
            
            # Redirect URL
            redirect_url = reverse('products:excel-import')
            
            # Import işlemini çağır
            with patch('os.unlink'):  # Dosya silme işlemini mock'la
                response = facade.handle_import_form(form, redirect_url)
            
            # Assertions
            self.assertEqual(response.status_code, 302)  # Redirect
            mock_manager.import_products.assert_called_once()
    
    @patch('products.views.excel_facade.ProductExcelManager')
    def test_excel_export_facade(self, mock_manager_class):
        """Export facade testi"""
        # Mock excel manager
        mock_manager = mock_manager_class.return_value
        mock_manager.export_products.return_value = self.excel_content
        
        # Excel Facade
        facade = ExcelExportFacade(self.request)
        
        # QuerySet
        queryset = Product.objects.all()
        
        # Export işlemi
        response = facade.export_products(queryset, export_type='full')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        mock_manager.export_products.assert_called_once_with(
            queryset, 
            export_type='full',
            use_chunks=False
        )
        
    @patch('products.views.excel_facade.ProductExcelManager')
    def test_excel_template_facade(self, mock_manager_class):
        """Template facade testi"""
        # Mock excel manager
        mock_manager = mock_manager_class.return_value
        mock_manager.generate_import_template.return_value = self.excel_content
        
        # Excel Facade
        facade = ExcelExportFacade(self.request)
        
        # Template oluştur
        response = facade.generate_template()
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('urun_import_template_', response['Content-Disposition'])
        mock_manager.generate_import_template.assert_called_once()