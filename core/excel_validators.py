"""
Validation pipeline for Excel import operations.
"""
from abc import ABC, abstractmethod
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import re
import logging

logger = logging.getLogger(__name__)


class ValidationResult:
    """Represents the result of a validation operation."""
    
    def __init__(self, is_valid=True, errors=None, warnings=None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning):
        self.warnings.append(warning)
    
    def merge(self, other):
        """Merge another validation result into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class BaseValidator(ABC):
    """Abstract base class for validators."""
    
    @abstractmethod
    def validate(self, data, row_num=None):
        """
        Validate data and return a ValidationResult.
        
        Args:
            data: Data to validate (dict or single value)
            row_num: Row number for error reporting
            
        Returns:
            ValidationResult instance
        """
        pass


class RequiredFieldValidator(BaseValidator):
    """Validates that required fields are present and not empty."""
    
    def __init__(self, required_fields):
        self.required_fields = required_fields
    
    def validate(self, data, row_num=None):
        result = ValidationResult()
        
        for field in self.required_fields:
            if field not in data or data[field] in [None, '', 'nan']:
                result.add_error({
                    'field': field,
                    'row': row_num,
                    'error_type': 'missing_required',
                    'message': _('Zorunlu alan eksik: {field}').format(field=field)
                })
        
        return result


class UniquenessValidator(BaseValidator):
    """Validates uniqueness of fields within the dataset."""
    
    def __init__(self, unique_fields):
        self.unique_fields = unique_fields
        self.seen_values = {field: set() for field in unique_fields}
    
    def validate(self, data, row_num=None):
        result = ValidationResult()
        
        for field in self.unique_fields:
            if field in data:
                value = data[field]
                if value in self.seen_values[field]:
                    result.add_error({
                        'field': field,
                        'row': row_num,
                        'value': value,
                        'error_type': 'duplicate_in_file',
                        'message': _('Dosyada tekrarlanan değer: {value}').format(value=value)
                    })
                else:
                    self.seen_values[field].add(value)
        
        return result


class PriceFormatValidator(BaseValidator):
    """Validates price format and converts to Decimal."""
    
    def validate(self, data, row_num=None):
        result = ValidationResult()
        price_fields = ['price', 'cost', 'unit_price', 'sale_price']
        
        for field in price_fields:
            if field in data and data[field] not in [None, '', 'nan']:
                try:
                    # Handle Turkish format (comma as decimal separator)
                    price_str = str(data[field]).replace(',', '.')
                    # Remove currency symbols and spaces
                    price_str = re.sub(r'[^\d.-]', '', price_str)
                    # Convert to Decimal
                    price = Decimal(price_str)
                    
                    if price < 0:
                        result.add_error({
                            'field': field,
                            'row': row_num,
                            'value': data[field],
                            'error_type': 'negative_price',
                            'message': _('Fiyat negatif olamaz')
                        })
                    
                    # Update data with cleaned value
                    data[field] = price
                    
                except (ValueError, TypeError):
                    result.add_error({
                        'field': field,
                        'row': row_num,
                        'value': data[field],
                        'error_type': 'invalid_price',
                        'message': _('Geçersiz fiyat formatı')
                    })
        
        return result


class EmailValidator(BaseValidator):
    """Validates email format."""
    
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate(self, data, row_num=None):
        result = ValidationResult()
        email_fields = ['email', 'customer_email', 'user_email']
        
        for field in email_fields:
            if field in data and data[field] not in [None, '', 'nan']:
                email = str(data[field]).strip()
                if not self.email_pattern.match(email):
                    result.add_error({
                        'field': field,
                        'row': row_num,
                        'value': data[field],
                        'error_type': 'invalid_email',
                        'message': _('Geçersiz email formatı')
                    })
        
        return result


class DateFormatValidator(BaseValidator):
    """Validates date format."""
    
    def __init__(self, date_format='%Y-%m-%d'):
        self.date_format = date_format
    
    def validate(self, data, row_num=None):
        from datetime import datetime
        
        result = ValidationResult()
        date_fields = ['date', 'order_date', 'created_at', 'sale_end_date']
        
        for field in date_fields:
            if field in data and data[field] not in [None, '', 'nan']:
                try:
                    # Try to parse date
                    if isinstance(data[field], str):
                        datetime.strptime(data[field], self.date_format)
                except ValueError:
                    result.add_error({
                        'field': field,
                        'row': row_num,
                        'value': data[field],
                        'error_type': 'invalid_date',
                        'message': _('Geçersiz tarih formatı. Format: {format}').format(
                            format=self.date_format
                        )
                    })
        
        return result


class ValidationPipeline:
    """Pipeline for running multiple validators."""
    
    def __init__(self):
        self.validators = []
    
    def add_validator(self, validator):
        """Add a validator to the pipeline."""
        if not isinstance(validator, BaseValidator):
            raise TypeError("Validator must be instance of BaseValidator")
        self.validators.append(validator)
        return self
    
    def validate(self, data, row_num=None):
        """
        Run all validators on the data.
        
        Args:
            data: Data to validate
            row_num: Row number for error reporting
            
        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult()
        
        for validator in self.validators:
            try:
                validator_result = validator.validate(data, row_num)
                result.merge(validator_result)
            except Exception as e:
                logger.error(f"Validator {validator.__class__.__name__} failed: {str(e)}")
                result.add_error({
                    'row': row_num,
                    'error_type': 'validation_error',
                    'message': str(e)
                })
        
        return result
    
    def validate_dataset(self, dataset):
        """
        Validate an entire dataset.
        
        Args:
            dataset: List of dictionaries or pandas DataFrame
            
        Returns:
            Dictionary with validation results
        """
        all_errors = []
        all_warnings = []
        valid_rows = []
        
        # Convert DataFrame to list of dicts if needed
        if hasattr(dataset, 'iterrows'):
            rows = [row.to_dict() for _, row in dataset.iterrows()]
        else:
            rows = dataset
        
        for idx, row in enumerate(rows):
            row_num = idx + 2  # Excel rows start at 1, plus header
            result = self.validate(row, row_num)
            
            if result.is_valid:
                valid_rows.append(row)
            else:
                all_errors.extend(result.errors)
            
            all_warnings.extend(result.warnings)
        
        return {
            'is_valid': len(all_errors) == 0,
            'valid_rows': valid_rows,
            'errors': all_errors,
            'warnings': all_warnings,
            'summary': {
                'total_rows': len(rows),
                'valid_rows': len(valid_rows),
                'error_count': len(all_errors),
                'warning_count': len(all_warnings)
            }
        }


# Pre-configured pipelines for common use cases

def get_product_import_pipeline():
    """Get a pre-configured pipeline for product imports."""
    pipeline = ValidationPipeline()
    pipeline.add_validator(RequiredFieldValidator(['sku', 'name', 'price']))
    pipeline.add_validator(UniquenessValidator(['sku']))
    pipeline.add_validator(PriceFormatValidator())
    pipeline.add_validator(EmailValidator())
    return pipeline


def get_order_import_pipeline():
    """Get a pre-configured pipeline for order imports."""
    pipeline = ValidationPipeline()
    pipeline.add_validator(RequiredFieldValidator(['order_number', 'customer_name', 'product_sku']))
    pipeline.add_validator(UniquenessValidator(['order_number']))
    pipeline.add_validator(PriceFormatValidator())
    pipeline.add_validator(DateFormatValidator())
    pipeline.add_validator(EmailValidator())
    return pipeline