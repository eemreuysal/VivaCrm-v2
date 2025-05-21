"""
Excel error handling test
"""
from django.test import TestCase
from decimal import Decimal

from core.excel_errors import (
    ValidationError, FormatError, DuplicateError,
    RequiredFieldError, DataTypeError, RangeError,
    ErrorCollector, SUGGESTIONS
)
from products.excel_validators import ProductExcelValidator
from products.models import Category, Product


class ExcelErrorHandlingTest(TestCase):
    """Excel hata yönetimi testleri"""
    
    def setUp(self):
        """Test verileri oluştur"""
        self.category = Category.objects.create(
            name="Elektronik",
            slug="elektronik"
        )
        
        self.existing_product = Product.objects.create(
            sku="EXISTING-001",
            name="Mevcut Ürün",
            category=self.category,
            price=Decimal("99.99")
        )
    
    def test_error_collector(self):
        """ErrorCollector sınıfı testleri"""
        collector = ErrorCollector()
        
        # Hata ekle
        error1 = ValidationError("Test hatası", row=1, column="A")
        collector.add_error(error1)
        
        # Uyarı ekle
        warning1 = ValidationError("Test uyarısı", row=2, column="B")
        collector.add_warning(warning1)
        
        # Kontroller
        self.assertTrue(collector.has_errors())
        self.assertTrue(collector.has_warnings())
        self.assertEqual(collector.get_error_count(), 1)
        self.assertEqual(collector.get_warning_count(), 1)
        
        # Özet kontrolü
        summary = collector.get_summary()
        self.assertEqual(summary['total_errors'], 1)
        self.assertEqual(summary['total_warnings'], 1)
    
    def test_product_validator_required_fields(self):
        """Zorunlu alan kontrolleri"""
        validator = ProductExcelValidator()
        
        # Boş satır
        row_data = {}
        cleaned_data = validator.validate_row(row_data, 2)
        
        # Zorunlu alan hataları kontrolü
        self.assertTrue(validator.error_collector.has_errors())
        errors = validator.error_collector.get_errors_by_type(RequiredFieldError)
        self.assertEqual(len(errors), 4)  # sku, name, category, price
    
    def test_product_validator_sku_format(self):
        """SKU format kontrolleri"""
        validator = ProductExcelValidator()
        
        # Geçersiz SKU - çok kısa
        row_data = {'sku': 'AB'}
        validator.validate_row(row_data, 2)
        
        errors = validator.error_collector.to_list()
        self.assertTrue(any(e['code'] == 'VALIDATION_ERROR' for e in errors))
        
        # Geçersiz SKU - özel karakterler
        validator = ProductExcelValidator()
        row_data = {'sku': 'ABC@123'}
        validator.validate_row(row_data, 2)
        
        errors = validator.error_collector.to_list()
        self.assertTrue(any(e['code'] == 'FORMAT_ERROR' for e in errors))
    
    def test_product_validator_duplicate_sku(self):
        """Tekrar eden SKU kontrolleri"""
        validator = ProductExcelValidator()
        
        # Mevcut SKU
        row_data = {'sku': 'EXISTING-001'}
        validator.validate_row(row_data, 2)
        
        errors = validator.error_collector.to_list()
        self.assertTrue(any(e['code'] == 'DUPLICATE_ERROR' for e in errors))
    
    def test_product_validator_price_format(self):
        """Fiyat format kontrolleri"""
        validator = ProductExcelValidator()
        
        # Geçersiz fiyat
        row_data = {'price': 'invalid'}
        validator.validate_row(row_data, 2)
        
        errors = validator.error_collector.to_list()
        self.assertTrue(any(e['code'] == 'FORMAT_ERROR' for e in errors))
        
        # Negatif fiyat
        validator = ProductExcelValidator()
        row_data = {'price': '-10.50'}
        validator.validate_row(row_data, 2)
        
        errors = validator.error_collector.to_list()
        self.assertTrue(any(e['code'] == 'RANGE_ERROR' for e in errors))
    
    def test_product_validator_category_reference(self):
        """Kategori referans kontrolleri"""
        validator = ProductExcelValidator()
        
        # Mevcut olmayan kategori
        row_data = {'category': 'Olmayan Kategori'}
        validator.validate_row(row_data, 2)
        
        errors = validator.error_collector.to_list()
        self.assertTrue(any(e['code'] == 'REFERENCE_ERROR' for e in errors))
        
        # Mevcut kategori
        validator = ProductExcelValidator()
        row_data = {'category': 'Elektronik'}
        cleaned = validator.validate_row(row_data, 2)
        
        self.assertIn('category', cleaned)
        self.assertEqual(cleaned['category'], self.category)
    
    def test_error_messages_turkish(self):
        """Türkçe hata mesajları kontrolü"""
        error = ValidationError(
            "Test mesajı",
            row=5,
            column="SKU",
            value="TEST-123",
            suggestion="Test önerisi"
        )
        
        formatted = error.get_formatted_message()
        self.assertIn("Satır 5", formatted)
        self.assertIn("Sütun SKU", formatted)
        self.assertIn("Test mesajı", formatted)
        self.assertIn("💡 Öneri: Test önerisi", formatted)
    
    def test_pandas_error_export(self):
        """Pandas DataFrame export kontrolü"""
        collector = ErrorCollector()
        
        error1 = ValidationError(
            "Test hatası 1",
            row=2,
            column="SKU",
            field="sku",
            value="TEST",
            suggestion="Öneri 1"
        )
        collector.add_error(error1)
        
        pandas_errors = collector.to_pandas_errors()
        self.assertEqual(len(pandas_errors), 1)
        
        error_dict = pandas_errors[0]
        self.assertEqual(error_dict['Satır'], 2)
        self.assertEqual(error_dict['Sütun'], 'SKU')
        self.assertEqual(error_dict['Alan'], 'sku')
        self.assertEqual(error_dict['Hata'], 'Test hatası 1')
        self.assertEqual(error_dict['Öneri'], 'Öneri 1')