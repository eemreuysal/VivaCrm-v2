"""
Merkezi Excel validasyon fonksiyonları.
DRY Principle: Tüm modüller bu validatörleri kullanır.
"""
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Optional, List, Union
import pandas as pd
from django.core.exceptions import ValidationError


class ExcelValidators:
    """
    Excel verisi için merkezi validasyon sınıfı.
    Static metodlar kullanarak state tutmadan validasyon yapar.
    """
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> Any:
        """Zorunlu alan kontrolü"""
        if pd.isna(value) or value is None:
            raise ValidationError(f"{field_name} boş olamaz")
            
        if isinstance(value, str) and not value.strip():
            raise ValidationError(f"{field_name} boş olamaz")
            
        return value
    
    @staticmethod
    def validate_decimal(
        value: Any, 
        field_name: str, 
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        allow_none: bool = True
    ) -> Optional[Decimal]:
        """
        Decimal validasyonu.
        Args:
            value: Doğrulanacak değer
            field_name: Alan adı (hata mesajları için)
            min_value: Minimum değer
            max_value: Maximum değer
            allow_none: None değere izin ver
        """
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        # String temizleme
        if isinstance(value, str):
            value = value.strip().replace(',', '.').replace(' ', '')
        
        try:
            decimal_value = Decimal(str(value))
            
            # Min/Max kontrolleri
            if min_value is not None and decimal_value < min_value:
                raise ValidationError(
                    f"{field_name} {min_value} değerinden küçük olamaz. "
                    f"Girilen değer: {decimal_value}"
                )
            
            if max_value is not None and decimal_value > max_value:
                raise ValidationError(
                    f"{field_name} {max_value} değerinden büyük olamaz. "
                    f"Girilen değer: {decimal_value}"
                )
            
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            raise ValidationError(f"{field_name} geçerli bir sayı değil: {value}")
    
    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        allow_none: bool = True
    ) -> Optional[int]:
        """Integer validasyonu"""
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        try:
            # Float değerleri integer'a çevir
            if isinstance(value, float):
                if value.is_integer():
                    int_value = int(value)
                else:
                    raise ValidationError(f"{field_name} tam sayı olmalı")
            else:
                int_value = int(value)
            
            # Min/Max kontrolleri
            if min_value is not None and int_value < min_value:
                raise ValidationError(
                    f"{field_name} {min_value} değerinden küçük olamaz. "
                    f"Girilen değer: {int_value}"
                )
            
            if max_value is not None and int_value > max_value:
                raise ValidationError(
                    f"{field_name} {max_value} değerinden büyük olamaz. "
                    f"Girilen değer: {int_value}"
                )
            
            return int_value
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"{field_name} geçerli bir tam sayı değil: {value}")
    
    @staticmethod
    def validate_date(
        value: Any,
        field_name: str,
        formats: Optional[List[str]] = None,
        allow_none: bool = True
    ) -> Optional[datetime]:
        """
        Tarih validasyonu.
        Farklı tarih formatlarını destekler.
        """
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        # Zaten datetime ise döndür
        if isinstance(value, datetime):
            return value
        
        # pd.Timestamp ise datetime'a çevir
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        
        # String olarak işle
        if not isinstance(value, str):
            value = str(value)
        
        # Varsayılan formatlar
        if formats is None:
            formats = [
                '%Y-%m-%d',
                '%d.%m.%Y',
                '%d/%m/%Y',
                '%Y/%m/%d',
                '%d-%m-%Y',
                '%Y-%m-%d %H:%M:%S',
                '%d.%m.%Y %H:%M:%S'
            ]
        
        # Formatları dene
        for date_format in formats:
            try:
                return datetime.strptime(value.strip(), date_format)
            except ValueError:
                continue
        
        # Hiçbir format uymadı
        raise ValidationError(
            f"{field_name} geçerli bir tarih değil: {value}. "
            f"Desteklenen formatlar: {', '.join(formats)}"
        )
    
    @staticmethod
    def validate_boolean(
        value: Any,
        field_name: str,
        true_values: Optional[List[str]] = None,
        false_values: Optional[List[str]] = None,
        allow_none: bool = True
    ) -> Optional[bool]:
        """
        Boolean validasyonu.
        Farklı dillerdeki true/false değerlerini destekler.
        """
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        # Zaten boolean ise döndür
        if isinstance(value, bool):
            return value
        
        # Varsayılan değerler
        if true_values is None:
            true_values = ['true', 'yes', 'evet', '1', 'doğru', 'aktif', 'var']
        
        if false_values is None:
            false_values = ['false', 'no', 'hayır', '0', 'yanlış', 'pasif', 'yok']
        
        # String'e çevir ve normalize et
        value_str = str(value).lower().strip()
        
        if value_str in true_values:
            return True
        elif value_str in false_values:
            return False
        else:
            raise ValidationError(
                f"{field_name} boolean değer olmalı. "
                f"Kabul edilen true değerleri: {', '.join(true_values)}. "
                f"Kabul edilen false değerleri: {', '.join(false_values)}. "
                f"Girilen değer: {value}"
            )
    
    @staticmethod
    def validate_choice(
        value: Any,
        field_name: str,
        choices: List[Union[str, tuple]],
        allow_none: bool = True
    ) -> Optional[str]:
        """
        Choice field validasyonu.
        Django choice field'ları için.
        """
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        value_str = str(value).strip()
        
        # Choices tuple listesi ise değerleri ayıkla
        valid_values = []
        for choice in choices:
            if isinstance(choice, tuple):
                valid_values.append(choice[0])
            else:
                valid_values.append(choice)
        
        if value_str not in valid_values:
            raise ValidationError(
                f"{field_name} geçersiz değer: '{value_str}'. "
                f"Geçerli değerler: {', '.join(map(str, valid_values))}"
            )
        
        return value_str
    
    @staticmethod
    def validate_email(value: Any, field_name: str, allow_none: bool = True) -> Optional[str]:
        """Email validasyonu"""
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        import re
        email_str = str(value).strip().lower()
        
        # Basit email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email_str):
            raise ValidationError(f"{field_name} geçerli bir email adresi değil: {value}")
        
        return email_str
    
    @staticmethod
    def validate_phone(value: Any, field_name: str, allow_none: bool = True) -> Optional[str]:
        """Telefon numarası validasyonu"""
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        import re
        phone_str = str(value).strip()
        
        # Sadece rakam, boşluk, +, -, (, ) karakterlerine izin ver
        phone_str = re.sub(r'[^\d\s+\-()]', '', phone_str)
        
        # En az 10 rakam olmalı
        digits_only = re.sub(r'\D', '', phone_str)
        if len(digits_only) < 10:
            raise ValidationError(
                f"{field_name} en az 10 rakam içermelidir. "
                f"Girilen değer: {value}"
            )
        
        return phone_str
    
    @staticmethod
    def validate_url(value: Any, field_name: str, allow_none: bool = True) -> Optional[str]:
        """URL validasyonu"""
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        from urllib.parse import urlparse
        url_str = str(value).strip()
        
        # HTTP/HTTPS ekle gerekirse
        if not url_str.startswith(('http://', 'https://')):
            url_str = 'https://' + url_str
        
        try:
            result = urlparse(url_str)
            if not all([result.scheme, result.netloc]):
                raise ValueError()
            return url_str
        except ValueError:
            raise ValidationError(f"{field_name} geçerli bir URL değil: {value}")
    
    @staticmethod
    def validate_length(
        value: Any,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        allow_none: bool = True
    ) -> Optional[str]:
        """String uzunluk validasyonu"""
        if pd.isna(value) or value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} boş olamaz")
        
        value_str = str(value).strip()
        length = len(value_str)
        
        if min_length is not None and length < min_length:
            raise ValidationError(
                f"{field_name} en az {min_length} karakter olmalı. "
                f"Girilen: {length} karakter"
            )
        
        if max_length is not None and length > max_length:
            raise ValidationError(
                f"{field_name} en fazla {max_length} karakter olabilir. "
                f"Girilen: {length} karakter"
            )
        
        return value_str