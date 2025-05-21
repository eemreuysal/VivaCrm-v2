"""
User-friendly error messages for Excel import operations.
"""
from django.utils.translation import gettext_lazy as _


class UserFriendlyErrorHandler:
    """
    Provides user-friendly error messages for Excel import errors.
    """
    
    ERROR_MESSAGES = {
        'duplicate_sku': _('Bu ürün kodu ({value}) zaten kayıtlı. Güncelleme yapmak için "Mevcut kayıtları güncelle" seçeneğini işaretleyin.'),
        'invalid_price': _('Geçersiz fiyat formatı: {value}. Ondalık ayırıcı olarak nokta kullanın (Örnek: 123.45)'),
        'missing_category': _('"{value}" kategorisi bulunamadı. Önce bu kategoriyi oluşturun veya mevcut bir kategori adı kullanın.'),
        'invalid_email': _('Geçersiz email formatı: {value}. Doğru format: ornek@domain.com'),
        'missing_required': _('Zorunlu alan boş bırakılamaz: {field}'),
        'invalid_date': _('Geçersiz tarih formatı: {value}. Kullanılması gereken format: YYYY-MM-DD'),
        'negative_stock': _('Stok miktarı negatif olamaz: {value}'),
        'invalid_tax_rate': _('Geçersiz KDV oranı: {value}. Geçerli oranlar: 1%, 8%, 18%'),
        'file_too_large': _('Dosya boyutu çok büyük. Maksimum boyut: {max_size}MB'),
        'invalid_file_format': _('Geçersiz dosya formatı. Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.'),
        'column_missing': _('Gerekli sütun bulunamadı: {column}'),
        'sku_format': _('SKU formatı hatalı: {value}. Özel karakterler ve boşluklar kaldırılmalı.'),
        'duplicate_in_file': _('Aynı {field} değeri dosyada birden fazla kez kullanılmış: {value}'),
        'invalid_boolean': _('Geçersiz boolean değeri: {value}. TRUE, FALSE, 1 veya 0 kullanın.'),
        'invalid_number': _('Geçersiz sayı formatı: {value}'),
        'category_not_found': _('"{value}" kategorisi bulunamadı. Önerilen kategori: {suggested}'),
        'product_not_found': _('SKU: {value} ile ürün bulunamadı'),
        'customer_not_found': _('Müşteri bulunamadı: {value}'),
        'invalid_status': _('Geçersiz durum: {value}. Geçerli değerler: {valid_values}'),
        'formula_not_supported': _('Excel formülleri desteklenmiyor. Lütfen değerleri manuel olarak girin: {cell}'),
        'encoding_error': _('Dosya karakter kodlaması hatalı. UTF-8 kodlaması kullanın.'),
        'sheet_not_found': _('Belirtilen sayfa bulunamadı: {sheet_name}'),
        'empty_file': _('Dosya boş veya veri içermiyor'),
        'permission_denied': _('Bu işlem için yetkiniz yok'),
        'system_error': _('Sistem hatası oluştu. Lütfen tekrar deneyin.')
    }
    
    COLUMN_TRANSLATIONS = {
        'tr': {
            'product_code': 'Ürün Kodu',
            'product_name': 'Ürün Adı',
            'category': 'Kategori',
            'price': 'Fiyat',
            'stock': 'Stok',
            'description': 'Açıklama',
            'tax_rate': 'KDV Oranı',
            'sku': 'SKU',
            'barcode': 'Barkod',
            'customer_name': 'Müşteri Adı',
            'order_date': 'Sipariş Tarihi',
            'quantity': 'Miktar',
            'unit_price': 'Birim Fiyat',
            'discount': 'İndirim'
        },
        'en': {
            'product_code': 'Product Code',
            'product_name': 'Product Name',
            'category': 'Category',
            'price': 'Price',
            'stock': 'Stock',
            'description': 'Description',
            'tax_rate': 'Tax Rate',
            'sku': 'SKU',
            'barcode': 'Barcode',
            'customer_name': 'Customer Name',
            'order_date': 'Order Date',
            'quantity': 'Quantity',
            'unit_price': 'Unit Price',
            'discount': 'Discount'
        }
    }
    
    def __init__(self, language='tr'):
        self.language = language
    
    def get_error_message(self, error_type, **kwargs):
        """
        Get a user-friendly error message.
        
        Args:
            error_type: Type of error
            **kwargs: Values to interpolate into the message
            
        Returns:
            Formatted error message
        """
        template = self.ERROR_MESSAGES.get(error_type, _('Bilinmeyen hata: {error_type}'))
        
        # Translate field names if needed
        if 'field' in kwargs:
            field_name = kwargs['field']
            translated_field = self.COLUMN_TRANSLATIONS.get(self.language, {}).get(field_name, field_name)
            kwargs['field'] = translated_field
        
        try:
            return str(template).format(**kwargs, error_type=error_type)
        except KeyError:
            return str(template)
    
    def get_column_name(self, field, language=None):
        """
        Get translated column name.
        
        Args:
            field: Field name
            language: Language code (default: instance language)
            
        Returns:
            Translated column name
        """
        lang = language or self.language
        return self.COLUMN_TRANSLATIONS.get(lang, {}).get(field, field)
    
    def format_error_report(self, errors):
        """
        Format a list of errors into a readable report.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Formatted error report string
        """
        if not errors:
            return _("Hata bulunmadı.")
        
        report_lines = [_("İçe Aktarma Hataları:")]
        
        # Group errors by type
        error_groups = {}
        for error in errors:
            error_type = error.get('error_type')
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)
        
        # Format each error group
        for error_type, group_errors in error_groups.items():
            report_lines.append(f"\n{self.get_error_message(error_type)}:")
            for error in group_errors[:5]:  # Show max 5 errors per type
                row = error.get('row', '?')
                field = error.get('field', '?')
                value = error.get('value', '')
                report_lines.append(f"  - Satır {row}, {field}: {value}")
            
            if len(group_errors) > 5:
                report_lines.append(f"  ... ve {len(group_errors) - 5} benzer hata daha")
        
        return '\n'.join(report_lines)