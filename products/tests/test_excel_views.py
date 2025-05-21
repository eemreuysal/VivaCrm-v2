"""
Excel views testleri.
Facade pattern implementasyonu ile oluşturulmuş view'lar test edilir.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Product, Category
from ..views.excel_facade import ExcelImportFacade, ExcelExportFacade

User = get_user_model()


class ExcelViewsTestCase(TestCase):
    """Excel view'larının testleri"""
    
    def setUp(self):
        """Test setup"""
        self.client = Client()
        
        # Test kullanıcısı oluştur
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(
            username=self.username,
            email='test@example.com',
            password=self.password
        )
        
        # Tüm izinleri ver
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Product)
        permissions = Permission.objects.filter(content_type=content_type)
        for permission in permissions:
            self.user.user_permissions.add(permission)
        
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
        
        # Test Excel dosyası
        self.excel_content = b'dummy content'  # Gerçek bir Excel dosyası olmalı
        self.excel_file = SimpleUploadedFile(
            "test.xlsx",
            self.excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Login
        self.client.login(username=self.username, password=self.password)
    
    def test_import_view_get(self):
        """Import sayfası GET testi"""
        url = reverse('excel-import')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/excel_import.html')
    
    @patch('products.views.excel_views.ExcelImportFacade')
    def test_import_view_post(self, mock_facade_class):
        """Import sayfası POST testi"""
        # Mock facade
        mock_facade = mock_facade_class.return_value
        mock_response = MagicMock()
        mock_facade.handle_import_form.return_value = mock_response
        
        # Import URL
        url = reverse('excel-import')
        
        # POST isteği
        form_data = {'use_chunks': True, 'skip_validation': False}
        response = self.client.post(
            url, 
            data=form_data,
            files={'excel_file': self.excel_file}
        )
        
        # Assertions
        mock_facade_class.assert_called_once()
        mock_facade.handle_import_form.assert_called_once()
    
    @patch('products.views.excel_views.ExcelImportFacade')
    def test_import_results_view(self, mock_facade_class):
        """Import sonuçları sayfası testi"""
        # Mock facade
        mock_facade = mock_facade_class.return_value
        mock_facade.get_import_results.return_value = {
            'results': {
                'total_rows': 10,
                'success_count': 8,
                'error_count': 2,
                'errors': []
            },
            'task': None,
            'session_id': 'test-session',
            'statistics': 'Test istatistikleri'
        }
        
        # Results URL
        url = reverse('excel-import-results', kwargs={'session_id': 'test-session'})
        
        # GET isteği
        response = self.client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/excel_import_results.html')
        mock_facade.get_import_results.assert_called_once_with('test-session')
    
    @patch('products.views.excel_views.ExcelExportFacade')
    def test_export_view(self, mock_facade_class):
        """Export sayfası testi"""
        # Mock facade
        mock_facade = mock_facade_class.return_value
        mock_response = MagicMock()
        mock_facade.export_products.return_value = mock_response
        
        # Export URL
        url = reverse('excel-export')
        
        # GET isteği
        response = self.client.get(url, {'type': 'full'})
        
        # Assertions
        mock_facade_class.assert_called_once()
        mock_facade.export_products.assert_called_once()
    
    @patch('products.views.excel_views.ExcelExportFacade')
    def test_template_view(self, mock_facade_class):
        """Template sayfası testi"""
        # Mock facade
        mock_facade = mock_facade_class.return_value
        mock_response = MagicMock()
        mock_facade.generate_template.return_value = mock_response
        
        # Template URL
        url = reverse('excel-template')
        
        # GET isteği
        response = self.client.get(url)
        
        # Assertions
        mock_facade_class.assert_called_once()
        mock_facade.generate_template.assert_called_once()
    
    @patch('products.views.excel_views.ExcelImportFacade')
    def test_validate_endpoint(self, mock_facade_class):
        """Validate AJAX endpoint testi"""
        # Mock facade
        mock_facade = mock_facade_class.return_value
        mock_facade.validate_excel_file.return_value = {
            'valid': True,
            'errors': [],
            'file_size': 1024,
            'estimated_rows': 10
        }
        
        # Validate URL
        url = reverse('excel-validate')
        
        # POST isteği
        response = self.client.post(
            url,
            files={'excel_file': self.excel_file}
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['valid'])
        mock_facade.validate_excel_file.assert_called_once()
    
    def test_progress_api_not_found(self):
        """Progress API - sonuç bulunamadı testi"""
        # Progress URL
        url = reverse('excel-progress', kwargs={'session_id': 'nonexistent-session'})
        
        # GET isteği
        response = self.client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, 404)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'not_found')