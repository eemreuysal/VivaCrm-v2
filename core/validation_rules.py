import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type, Dict
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ValidationRule(ABC):
    """Abstract base class for validation rules"""
    
    def __init__(self, error_message: Optional[str] = None):
        self.error_message = error_message or self.get_default_error()
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate the given value"""
        pass
    
    @abstractmethod
    def get_default_error(self) -> str:
        """Get default error message"""
        pass
    
    def get_error_message(self) -> str:
        """Get error message for validation failure"""
        return self.error_message


class RegexRule(ValidationRule):
    """Regex pattern validation rule"""
    
    def __init__(self, pattern: str, error_message: Optional[str] = None):
        self.pattern = pattern
        self.compiled_pattern = re.compile(pattern)
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        return bool(self.compiled_pattern.match(str(value)))
    
    def get_default_error(self) -> str:
        return _("Değer geçerli format ile eşleşmiyor")


class RangeRule(ValidationRule):
    """Numeric range validation rule"""
    
    def __init__(self, min_value: Optional[float] = None, 
                 max_value: Optional[float] = None,
                 error_message: Optional[str] = None):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        try:
            numeric_value = float(value)
            if self.min_value is not None and numeric_value < self.min_value:
                return False
            if self.max_value is not None and numeric_value > self.max_value:
                return False
            return True
        except (TypeError, ValueError):
            return False
    
    def get_default_error(self) -> str:
        if self.min_value is not None and self.max_value is not None:
            return _(f"Değer {self.min_value} ile {self.max_value} arasında olmalıdır")
        elif self.min_value is not None:
            return _(f"Değer {self.min_value} veya daha büyük olmalıdır")
        elif self.max_value is not None:
            return _(f"Değer {self.max_value} veya daha küçük olmalıdır")
        return _("Geçersiz sayısal değer")


class ListRule(ValidationRule):
    """List of allowed values validation rule"""
    
    def __init__(self, allowed_values: List[Any], error_message: Optional[str] = None):
        self.allowed_values = allowed_values
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        return value in self.allowed_values
    
    def get_default_error(self) -> str:
        return _(f"Değer şunlardan biri olmalıdır: {', '.join(map(str, self.allowed_values))}")


class LengthRule(ValidationRule):
    """String length validation rule"""
    
    def __init__(self, min_length: Optional[int] = None,
                 max_length: Optional[int] = None,
                 error_message: Optional[str] = None):
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        length = len(str(value))
        if self.min_length is not None and length < self.min_length:
            return False
        if self.max_length is not None and length > self.max_length:
            return False
        return True
    
    def get_default_error(self) -> str:
        if self.min_length is not None and self.max_length is not None:
            return _(f"Uzunluk {self.min_length} ile {self.max_length} karakter arasında olmalıdır")
        elif self.min_length is not None:
            return _(f"En az {self.min_length} karakter olmalıdır")
        elif self.max_length is not None:
            return _(f"En fazla {self.max_length} karakter olmalıdır")
        return _("Geçersiz uzunluk")


class EmailRule(ValidationRule):
    """Email validation rule"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(error_message)
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        return bool(self.email_pattern.match(str(value)))
    
    def get_default_error(self) -> str:
        return _("Geçerli bir email adresi giriniz")


class PhoneRule(ValidationRule):
    """Turkish phone number validation rule"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(error_message)
        self.phone_pattern = re.compile(r'^(0)?[1-9][0-9]{9}$')
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        # Remove spaces and dashes
        cleaned = str(value).replace(' ', '').replace('-', '')
        return bool(self.phone_pattern.match(cleaned))
    
    def get_default_error(self) -> str:
        return _("Geçerli bir telefon numarası giriniz")


class TCKNRule(ValidationRule):
    """Turkish ID number validation rule"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        tckn = str(value)
        
        # Check length
        if len(tckn) != 11:
            return False
        
        # Check if all digits
        if not tckn.isdigit():
            return False
        
        # Check first digit
        if tckn[0] == '0':
            return False
        
        # Calculate checksums
        digits = [int(d) for d in tckn]
        
        # First checksum
        odd_sum = sum(digits[0:9:2])
        even_sum = sum(digits[1:8:2])
        checksum1 = (odd_sum * 7 - even_sum) % 10
        
        if checksum1 != digits[9]:
            return False
        
        # Second checksum
        checksum2 = sum(digits[0:10]) % 10
        
        return checksum2 == digits[10]
    
    def get_default_error(self) -> str:
        return _("Geçerli bir TC Kimlik Numarası giriniz")


class RequiredRule(ValidationRule):
    """Required field validation rule"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True
    
    def get_default_error(self) -> str:
        return _("Bu alan zorunludur")


class NumericRule(ValidationRule):
    """Numeric value validation rule"""
    
    def __init__(self, error_message: Optional[str] = None):
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
    
    def get_default_error(self) -> str:
        return _("Sayısal bir değer giriniz")


class DateRule(ValidationRule):
    """Date validation rule"""
    
    def __init__(self, format: str = '%Y-%m-%d', error_message: Optional[str] = None):
        self.format = format
        super().__init__(error_message)
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        try:
            from datetime import datetime
            datetime.strptime(str(value), self.format)
            return True
        except ValueError:
            return False
    
    def get_default_error(self) -> str:
        return _(f"Tarih formatı {self.format} olmalıdır")


class RuleBuilder:
    """Builder class for creating validation rules"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
    
    def required(self, error_message: Optional[str] = None):
        """Add required rule"""
        self.rules.append(RequiredRule(error_message))
        return self
    
    def regex(self, pattern: str, error_message: Optional[str] = None):
        """Add regex rule"""
        self.rules.append(RegexRule(pattern, error_message))
        return self
    
    def range(self, min_value: Optional[float] = None,
              max_value: Optional[float] = None,
              error_message: Optional[str] = None):
        """Add range rule"""
        self.rules.append(RangeRule(min_value, max_value, error_message))
        return self
    
    def list(self, allowed_values: List[Any], error_message: Optional[str] = None):
        """Add list rule"""
        self.rules.append(ListRule(allowed_values, error_message))
        return self
    
    def length(self, min_length: Optional[int] = None,
               max_length: Optional[int] = None,
               error_message: Optional[str] = None):
        """Add length rule"""
        self.rules.append(LengthRule(min_length, max_length, error_message))
        return self
    
    def email(self, error_message: Optional[str] = None):
        """Add email rule"""
        self.rules.append(EmailRule(error_message))
        return self
    
    def phone(self, error_message: Optional[str] = None):
        """Add phone rule"""
        self.rules.append(PhoneRule(error_message))
        return self
    
    def tckn(self, error_message: Optional[str] = None):
        """Add TCKN rule"""
        self.rules.append(TCKNRule(error_message))
        return self
    
    def numeric(self, error_message: Optional[str] = None):
        """Add numeric rule"""
        self.rules.append(NumericRule(error_message))
        return self
    
    def date(self, format: str = '%Y-%m-%d', error_message: Optional[str] = None):
        """Add date rule"""
        self.rules.append(DateRule(format, error_message))
        return self
    
    def build(self) -> List[ValidationRule]:
        """Build and return list of rules"""
        return self.rules


class RuleRegistry:
    """Registry for storing and retrieving validation rules"""
    
    _rules: Dict[str, Type[ValidationRule]] = {
        'required': RequiredRule,
        'regex': RegexRule,
        'range': RangeRule,
        'list': ListRule,
        'length': LengthRule,
        'email': EmailRule,
        'phone': PhoneRule,
        'tckn': TCKNRule,
        'numeric': NumericRule,
        'date': DateRule,
    }
    
    @classmethod
    def register(cls, name: str, rule_class: Type[ValidationRule]):
        """Register a new rule type"""
        cls._rules[name] = rule_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[ValidationRule]]:
        """Get rule class by name"""
        return cls._rules.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, Type[ValidationRule]]:
        """Get all registered rules"""
        return cls._rules.copy()


class Validator:
    """Main validator class"""
    
    def __init__(self, rules: List[ValidationRule]):
        self.rules = rules
    
    def validate(self, value: Any) -> None:
        """Validate value against all rules"""
        for rule in self.rules:
            if not rule.validate(value):
                raise ValidationError(rule.get_error_message())
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without raising exception"""
        try:
            self.validate(value)
            return True
        except ValidationError:
            return False


class PresetRules:
    """Hazır doğrulama kuralları"""
    
    PHONE_RULE = RequiredRule(error_message='Telefon numarası zorunludur')
    EMAIL_RULE = RequiredRule(error_message='Email adresi zorunludur')
    TC_NO_RULE = RequiredRule(error_message='TC Kimlik no zorunludur')
    
    @classmethod
    def get_all(cls):
        """Tüm hazır kuralları getir"""
        return {
            'phone': cls.PHONE_RULE,
            'email': cls.EMAIL_RULE,
            'tc_no': cls.TC_NO_RULE,
        }
    
    @classmethod
    def create_rule(cls, name: str, rule_type: str, **kwargs):
        """Dinamik kural oluştur"""
        rule_class = RuleRegistry.get(rule_type)
        if not rule_class:
            raise ValueError(f"Unknown rule type: {rule_type}")
        
        return rule_class(**kwargs)
    
    @classmethod
    def turkish_phone(cls):
        """Türkçe telefon numarası doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("Telefon numarası zorunludur")) \
            .phone(_("Geçersiz telefon numarası formatı"))
    
    @classmethod
    def email_address(cls):
        """Email adresi doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("Email adresi zorunludur")) \
            .email(_("Geçersiz email formatı"))
    
    @classmethod
    def turkish_id(cls):
        """TC Kimlik numarası doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("TC Kimlik numarası zorunludur")) \
            .tckn(_("Geçersiz TC Kimlik numarası"))
    
    @classmethod
    def price_field(cls):
        """Fiyat alanı doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("Fiyat alanı zorunludur")) \
            .numeric(_("Fiyat sayısal bir değer olmalıdır")) \
            .range(min_value=0, error_message=_("Fiyat 0'dan büyük olmalıdır"))
    
    @classmethod
    def percentage(cls):
        """Yüzde alanı doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("Yüzde alanı zorunludur")) \
            .numeric(_("Yüzde sayısal bir değer olmalıdır")) \
            .range(min_value=0, max_value=100, error_message=_("Yüzde 0-100 arasında olmalıdır"))
    
    @classmethod
    def stock_quantity(cls):
        """Stok miktarı doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("Stok miktarı zorunludur")) \
            .numeric(_("Stok miktarı sayısal bir değer olmalıdır")) \
            .range(min_value=0, error_message=_("Stok miktarı 0 veya daha büyük olmalıdır"))
    
    @classmethod
    def website_url(cls):
        """Website URL doğrulama kuralları"""
        return RuleBuilder() \
            .regex(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(/[-\w%!$&\'()*+,;=:]+)*$', 
                  _("Geçerli bir URL giriniz"))
    
    @classmethod
    def company_name(cls):
        """Şirket adı doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("Şirket adı zorunludur")) \
            .length(min_length=2, max_length=255, error_message=_("Şirket adı 2-255 karakter arasında olmalıdır"))
    
    @classmethod
    def tax_number(cls):
        """Vergi numarası doğrulama kuralları"""
        return RuleBuilder() \
            .required(_("Vergi numarası zorunludur")) \
            .length(min_length=10, max_length=10, error_message=_("Vergi numarası 10 haneli olmalıdır")) \
            .numeric(_("Vergi numarası sadece rakamlardan oluşmalıdır"))
