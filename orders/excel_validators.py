"""
Sipariş Excel import doğrulayıcıları - Yeni format için güncellenmiş
"""
import re
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any

from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError

from customers.models import Customer
from products.models import Product
from orders.models import Order


class OrderExcelValidator:
    """Sipariş Excel import doğrulayıcı - Yeni Türkçe format için"""
    
    def __init__(self):
        self.errors = []
        self._customers_cache = {}
        self._products_cache = {}
        # Excel import için error collector ekle
        from core.excel_errors import ExcelErrorHandler
        self.error_collector = ExcelErrorHandler()
    
    def validate_file(self, df):
        """Dosya seviyesi doğrulama"""
        from core.excel_errors import ERROR_DEFINITIONS
        
        # Yeni format için gerekli sütunlar
        required_columns = [
            "SIPARIŞ TARIHI VE SAATI", 
            "SIPARIŞ NO", 
            "MÜŞTERI ISMI", 
            "SKU", 
            "ÜRÜN ISMI", 
            "ADET", 
            "BIRIM FIYAT"
        ]
        
        # Opsiyonel sütunlar
        optional_columns = [
            "EYALET", 
            "ŞEHIR", 
            "GTIN", 
            "BIRIM INDIRIM", 
            "SATIR FIYAT"
        ]
        
        # DataFrame'deki sütunları kontrol et
        df_columns = df.columns.tolist()
        missing_columns = []
        
        for col in required_columns:
            if col not in df_columns:
                missing_columns.append(col)
        
        if missing_columns:
            # Debug için sütun isimlerini yazdır
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"DataFrame columns: {df_columns}")
            logger.info(f"Missing columns: {missing_columns}")
            
            for col in missing_columns:
                self.error_collector.add_error(
                    error_key='MISSING_COLUMN',
                    row=0,
                    column=col,
                    value=None,
                    extra_data={
                        "columns": missing_columns,
                        "available_columns": df_columns
                    }
                )
            return False
        
        return True
    
    def validate_row(self, row_data: dict, row_number: int) -> dict:
        """Satır doğrulama - yeni format için"""
        cleaned_data = {'row_number': row_number}
        
        # Tarih doğrulama ve dönüştürme
        date_str = row_data.get("SIPARIŞ TARIHI VE SAATI")
        if not date_str:
            self.error_collector.add_error(
                error_key='required_field',
                row=row_number,
                column='SIPARIŞ TARIHI VE SAATI',
                value=None,
                extra_data={"message": "Sipariş tarihi gereklidir"}
            )
        else:
            try:
                # DD.MM.YYYY HH:MM formatını parse et
                if isinstance(date_str, str):
                    cleaned_data['order_date'] = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
                else:
                    # Pandas datetime object ise direkt kullan
                    cleaned_data['order_date'] = date_str
            except:
                self.error_collector.add_error(
                    error_key='invalid_date',
                    row=row_number,
                    column='SIPARIŞ TARIHI VE SAATI',
                    value=date_str,
                    extra_data={"message": "Geçersiz tarih formatı. GG.AA.YYYY SS:DD formatında olmalı"}
                )
        
        # Sipariş numarası
        order_no = row_data.get("SIPARIŞ NO")
        if not order_no:
            self.error_collector.add_error(
                error_key='required_field',
                row=row_number,
                column='SIPARIŞ NO',
                value=None,
                extra_data={"message": "Sipariş numarası gereklidir"}
            )
        else:
            cleaned_data['order_number'] = str(order_no)
        
        # Müşteri ismi
        customer_name = row_data.get("MÜŞTERI ISMI")
        if not customer_name:
            self.error_collector.add_error(
                error_key='required_field',
                row=row_number,
                column='MÜŞTERI ISMI',
                value=None,
                extra_data={"message": "Müşteri ismi gereklidir"}
            )
        else:
            cleaned_data['customer_name'] = customer_name
            # Optional fields
            cleaned_data['state'] = row_data.get("EYALET", "")
            cleaned_data['city'] = row_data.get("ŞEHIR", "")
        
        # Ürün bilgileri
        sku = row_data.get("SKU")
        if not sku:
            self.error_collector.add_error(
                error_key='required_field',
                row=row_number,
                column='SKU',
                value=None,
                extra_data={"message": "Ürün SKU gereklidir"}
            )
        else:
            cleaned_data['product_sku'] = str(sku)
            cleaned_data['product_gtin'] = row_data.get("GTIN", "")
        
        product_name = row_data.get("ÜRÜN ISMI")
        if not product_name:
            self.error_collector.add_error(
                error_key='required_field',
                row=row_number,
                column='ÜRÜN ISMI',
                value=None,
                extra_data={"message": "Ürün ismi gereklidir"}
            )
        else:
            cleaned_data['product_name'] = product_name
        
        # Miktar
        quantity = row_data.get("ADET")
        if quantity is None:
            self.error_collector.add_error(
                error_key='required_field',
                row=row_number,
                column='ADET',
                value=None,
                extra_data={"message": "Miktar gereklidir"}
            )
        else:
            try:
                cleaned_data['quantity'] = int(quantity)
                if cleaned_data['quantity'] < 1:
                    raise ValueError("Miktar 0'dan büyük olmalıdır")
            except:
                self.error_collector.add_error(
                    error_key='invalid_number',
                    row=row_number,
                    column='ADET',
                    value=quantity,
                    extra_data={"message": "Geçersiz miktar değeri"}
                )
        
        # Fiyat (virgül yerine nokta kullan)
        unit_price = row_data.get("BIRIM FIYAT")
        if unit_price is None:
            self.error_collector.add_error(
                error_key='required_field',
                row=row_number,
                column='BIRIM FIYAT',
                value=None,
                extra_data={"message": "Birim fiyat gereklidir"}
            )
        else:
            try:
                # Virgülü nokta ile değiştir
                price_str = str(unit_price).replace(',', '.')
                cleaned_data['unit_price'] = Decimal(price_str)
                if cleaned_data['unit_price'] < 0:
                    raise ValueError("Fiyat negatif olamaz")
            except:
                self.error_collector.add_error(
                    error_key='invalid_price',
                    row=row_number,
                    column='BIRIM FIYAT',
                    value=unit_price,
                    extra_data={"message": "Geçersiz fiyat formatı"}
                )
        
        # İndirim (optional)
        discount = row_data.get("BIRIM INDIRIM")
        if discount is not None and str(discount).strip():
            try:
                discount_str = str(discount).replace(',', '.')
                cleaned_data['discount_amount'] = Decimal(discount_str)
                if cleaned_data['discount_amount'] < 0:
                    raise ValueError("İndirim negatif olamaz")
            except:
                self.error_collector.add_error(
                    error_key='invalid_number',
                    row=row_number,
                    column='BIRIM INDIRIM',
                    value=discount,
                    extra_data={"message": "Geçersiz indirim formatı"}
                )
        else:
            cleaned_data['discount_amount'] = Decimal('0')
        
        # Satır fiyat (optional - kontrol için kullanılabilir)
        line_price = row_data.get("SATIR FIYAT")
        if line_price is not None and str(line_price).strip():
            try:
                line_price_str = str(line_price).replace(',', '.')
                cleaned_data['line_price'] = Decimal(line_price_str)
            except:
                # Satır fiyat opsiyonel olduğu için sadece uyarı
                pass
        
        return cleaned_data
    
    def has_errors(self) -> bool:
        """Hata var mı?"""
        return self.error_collector.has_errors() or len(self.errors) > 0
    
    def get_errors(self) -> list:
        """Hataları getir"""
        return self.errors