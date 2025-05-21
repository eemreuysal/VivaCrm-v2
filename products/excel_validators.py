"""
Ürün Excel import doğrulayıcıları - Basitleştirilmiş versiyon
"""
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from typing import Optional, List

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator

from products.models import Product, Category


class ProductExcelValidator:
    """Ürün Excel import doğrulayıcı - Basitleştirilmiş"""
    
    def __init__(self):
        self.errors = []
        self._existing_skus = set(Product.objects.values_list('sku', flat=True))
        self._categories = {cat.name: cat for cat in Category.objects.all()}
        self._processed_skus = set()
    
    def validate_row(self, row_data: dict, row_number: int) -> dict:
        """Satır doğrulama - basit versiyon"""
        cleaned_data = {'row_number': row_number}
        
        # Basit doğrulama
        if not row_data.get('sku'):
            self.errors.append({
                'row': row_number,
                'error': 'SKU alanı gereklidir'
            })
        
        if not row_data.get('name'):
            self.errors.append({
                'row': row_number,
                'error': 'Ürün adı gereklidir'
            })
        
        if not row_data.get('price'):
            self.errors.append({
                'row': row_number,
                'error': 'Fiyat alanı gereklidir'
            })
        
        if not row_data.get('category'):
            self.errors.append({
                'row': row_number,
                'error': 'Kategori alanı gereklidir'
            })
        
        return cleaned_data
    
    def has_errors(self) -> bool:
        """Hata var mı?"""
        return len(self.errors) > 0
    
    def get_errors(self) -> list:
        """Hataları getir"""
        return self.errors