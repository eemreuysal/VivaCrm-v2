from typing import Any, Dict, List, Type, Optional
import json
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.forms import Field, CharField, EmailField, URLField, IntegerField, DecimalField, DateField, DateTimeField, BooleanField
from django.core.validators import validate_email, URLValidator


class CustomFieldRegistry:
    """Registry for custom field types"""
    _registry: Dict[str, Type['CustomFieldType']] = {}
    
    @classmethod
    def register(cls, field_type: str, field_class: Type['CustomFieldType']):
        """Register a custom field type"""
        cls._registry[field_type] = field_class
    
    @classmethod
    def get(cls, field_type: str) -> Optional[Type['CustomFieldType']]:
        """Get a custom field type by name"""
        return cls._registry.get(field_type)
    
    @classmethod
    def get_choices(cls) -> List[tuple]:
        """Get choices for field type selection"""
        return [(key, field.display_name) for key, field in cls._registry.items()]


class CustomFieldType:
    """Base class for custom field types"""
    field_type = None
    display_name = None
    form_field_class = CharField
    model_field_class = models.CharField
    
    def __init__(self, field_definition: 'CustomFieldDefinition'):
        self.field_definition = field_definition
        self.options = field_definition.options or {}
    
    def validate(self, value: Any) -> None:
        """Validate the field value"""
        if value is None and self.field_definition.required:
            raise ValidationError("Bu alan zorunludur.")
    
    def clean(self, value: Any) -> Any:
        """Clean and normalize the field value"""
        if value is None:
            return None
        return value
    
    def convert_to_db_value(self, value: Any) -> Any:
        """Convert value for database storage"""
        return value
    
    def convert_from_db_value(self, value: Any) -> Any:
        """Convert value from database storage"""
        return value
    
    def get_form_field(self, **kwargs) -> Field:
        """Get Django form field instance"""
        field_kwargs = {
            'required': self.field_definition.required,
            'label': self.field_definition.label,
            'help_text': self.field_definition.help_text,
        }
        field_kwargs.update(kwargs)
        return self.form_field_class(**field_kwargs)
    
    def get_model_field(self, **kwargs) -> models.Field:
        """Get Django model field instance"""
        field_kwargs = {
            'blank': not self.field_definition.required,
            'null': not self.field_definition.required,
            'verbose_name': self.field_definition.label,
            'help_text': self.field_definition.help_text,
        }
        field_kwargs.update(kwargs)
        return self.model_field_class(**field_kwargs)


class TextFieldType(CustomFieldType):
    field_type = 'text'
    display_name = 'Metin'
    form_field_class = CharField
    model_field_class = models.CharField
    
    def get_model_field(self, **kwargs):
        max_length = self.options.get('max_length', 255)
        kwargs['max_length'] = max_length
        return super().get_model_field(**kwargs)


class LongTextFieldType(CustomFieldType):
    field_type = 'longtext'
    display_name = 'Uzun Metin'
    form_field_class = CharField
    model_field_class = models.TextField
    
    def get_form_field(self, **kwargs):
        kwargs['widget'] = kwargs.get('widget') or forms.Textarea
        return super().get_form_field(**kwargs)


class EmailFieldType(CustomFieldType):
    field_type = 'email'
    display_name = 'E-posta'
    form_field_class = EmailField
    model_field_class = models.EmailField
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value:
            try:
                validate_email(value)
            except ValidationError:
                raise ValidationError("Geçerli bir e-posta adresi girin.")


class URLFieldType(CustomFieldType):
    field_type = 'url'
    display_name = 'URL'
    form_field_class = URLField
    model_field_class = models.URLField
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value:
            validator = URLValidator()
            try:
                validator(value)
            except ValidationError:
                raise ValidationError("Geçerli bir URL girin.")


class PhoneFieldType(CustomFieldType):
    field_type = 'phone'
    display_name = 'Telefon'
    form_field_class = CharField
    model_field_class = models.CharField
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value:
            # Turkish phone number validation
            pattern = r'^(\+90|0)?[1-9]\d{9}$'
            if not re.match(pattern, value.replace(' ', '').replace('-', '')):
                raise ValidationError("Geçerli bir telefon numarası girin.")
    
    def clean(self, value: Any) -> Any:
        if value:
            # Normalize phone number
            value = value.replace(' ', '').replace('-', '')
            if value.startswith('0'):
                value = '+90' + value[1:]
            elif not value.startswith('+'):
                value = '+90' + value
        return value
    
    def get_model_field(self, **kwargs):
        kwargs['max_length'] = 20
        return super().get_model_field(**kwargs)


class BarcodeFieldType(CustomFieldType):
    field_type = 'barcode'
    display_name = 'Barkod'
    form_field_class = CharField
    model_field_class = models.CharField
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value:
            barcode_type = self.options.get('barcode_type', 'EAN13')
            if barcode_type == 'EAN13' and len(value) != 13:
                raise ValidationError("EAN13 barkodu 13 haneli olmalıdır.")
            elif barcode_type == 'EAN8' and len(value) != 8:
                raise ValidationError("EAN8 barkodu 8 haneli olmalıdır.")
            
            # Validate that it's numeric
            if not value.isdigit():
                raise ValidationError("Barkod sadece rakamlardan oluşmalıdır.")
    
    def get_model_field(self, **kwargs):
        barcode_type = self.options.get('barcode_type', 'EAN13')
        max_length = 13 if barcode_type == 'EAN13' else 8
        kwargs['max_length'] = max_length
        return super().get_model_field(**kwargs)


class NumberFieldType(CustomFieldType):
    field_type = 'number'
    display_name = 'Sayı'
    form_field_class = IntegerField
    model_field_class = models.IntegerField
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            try:
                int(value)
            except (ValueError, TypeError):
                raise ValidationError("Geçerli bir tam sayı girin.")
            
            min_value = self.options.get('min_value')
            max_value = self.options.get('max_value')
            
            if min_value is not None and value < min_value:
                raise ValidationError(f"Değer {min_value} veya daha büyük olmalıdır.")
            
            if max_value is not None and value > max_value:
                raise ValidationError(f"Değer {max_value} veya daha küçük olmalıdır.")
    
    def clean(self, value: Any) -> Any:
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return value


class DecimalFieldType(CustomFieldType):
    field_type = 'decimal'
    display_name = 'Ondalıklı Sayı'
    form_field_class = DecimalField
    model_field_class = models.DecimalField
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None:
            try:
                float(value)
            except (ValueError, TypeError):
                raise ValidationError("Geçerli bir ondalıklı sayı girin.")
    
    def get_model_field(self, **kwargs):
        kwargs['max_digits'] = self.options.get('max_digits', 10)
        kwargs['decimal_places'] = self.options.get('decimal_places', 2)
        return super().get_model_field(**kwargs)


class BooleanFieldType(CustomFieldType):
    field_type = 'boolean'
    display_name = 'Evet/Hayır'
    form_field_class = BooleanField
    model_field_class = models.BooleanField
    
    def get_model_field(self, **kwargs):
        kwargs['default'] = self.options.get('default_value', False)
        return super().get_model_field(**kwargs)


class DateFieldType(CustomFieldType):
    field_type = 'date'
    display_name = 'Tarih'
    form_field_class = DateField
    model_field_class = models.DateField


class DateTimeFieldType(CustomFieldType):
    field_type = 'datetime'
    display_name = 'Tarih ve Saat'
    form_field_class = DateTimeField
    model_field_class = models.DateTimeField


class ChoiceFieldType(CustomFieldType):
    field_type = 'choice'
    display_name = 'Seçim Listesi'
    form_field_class = CharField
    model_field_class = models.CharField
    
    def get_choices(self):
        """Get choices from options"""
        choices_str = self.options.get('choices', '')
        choices = []
        for line in choices_str.strip().split('\n'):
            if '|' in line:
                value, label = line.split('|', 1)
                choices.append((value.strip(), label.strip()))
            else:
                choices.append((line.strip(), line.strip()))
        return choices
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value:
            valid_values = [choice[0] for choice in self.get_choices()]
            if value not in valid_values:
                raise ValidationError("Geçersiz seçim.")
    
    def get_form_field(self, **kwargs):
        from django import forms
        kwargs['widget'] = forms.Select
        kwargs['choices'] = self.get_choices()
        return forms.ChoiceField(**kwargs)
    
    def get_model_field(self, **kwargs):
        kwargs['max_length'] = 100
        kwargs['choices'] = self.get_choices()
        return super().get_model_field(**kwargs)


class JSONFieldType(CustomFieldType):
    field_type = 'json'
    display_name = 'JSON Veri'
    form_field_class = CharField
    model_field_class = models.JSONField
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value:
            try:
                if isinstance(value, str):
                    json.loads(value)
            except (ValueError, TypeError):
                raise ValidationError("Geçerli JSON verisi girin.")
    
    def clean(self, value: Any) -> Any:
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return None
        return value
    
    def get_form_field(self, **kwargs):
        from django import forms
        kwargs['widget'] = forms.Textarea
        return super().get_form_field(**kwargs)


# Register all field types
CustomFieldRegistry.register('text', TextFieldType)
CustomFieldRegistry.register('longtext', LongTextFieldType)
CustomFieldRegistry.register('email', EmailFieldType)
CustomFieldRegistry.register('url', URLFieldType)
CustomFieldRegistry.register('phone', PhoneFieldType)
CustomFieldRegistry.register('barcode', BarcodeFieldType)
CustomFieldRegistry.register('number', NumberFieldType)
CustomFieldRegistry.register('decimal', DecimalFieldType)
CustomFieldRegistry.register('boolean', BooleanFieldType)
CustomFieldRegistry.register('date', DateFieldType)
CustomFieldRegistry.register('datetime', DateTimeFieldType)
CustomFieldRegistry.register('choice', ChoiceFieldType)
CustomFieldRegistry.register('json', JSONFieldType)


class CustomFieldMixin:
    """Mixin for models that support custom fields"""
    
    def get_custom_fields(self):
        """Get custom field definitions for this model"""
        from core.models import CustomFieldDefinition
        model_name = self.__class__.__name__.lower()
        return CustomFieldDefinition.objects.filter(
            model_name=model_name,
            is_active=True
        ).order_by('order')
    
    def get_custom_field_value(self, field_name: str) -> Any:
        """Get custom field value"""
        if hasattr(self, 'custom_fields') and self.custom_fields:
            return self.custom_fields.get(field_name)
        return None
    
    def set_custom_field_value(self, field_name: str, value: Any):
        """Set custom field value"""
        if not hasattr(self, 'custom_fields'):
            self.custom_fields = {}
        
        # Validate and clean the value
        field_def = self.get_custom_fields().filter(field_name=field_name).first()
        if field_def:
            field_type_class = CustomFieldRegistry.get(field_def.field_type)
            if field_type_class:
                field_instance = field_type_class(field_def)
                field_instance.validate(value)
                value = field_instance.clean(value)
        
        self.custom_fields[field_name] = value
    
    def validate_custom_fields(self):
        """Validate all custom fields"""
        for field_def in self.get_custom_fields():
            value = self.get_custom_field_value(field_def.field_name)
            field_type_class = CustomFieldRegistry.get(field_def.field_type)
            if field_type_class:
                field_instance = field_type_class(field_def)
                field_instance.validate(value)