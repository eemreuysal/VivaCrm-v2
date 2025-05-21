# VivaCRM Excel Error Handling System

## Overview

This document describes the comprehensive error handling system for Excel imports in VivaCRM. The system provides detailed validation, user-friendly error messages in Turkish, and error recovery suggestions.

## Architecture

### Core Components

1. **Error Classes** (`core/excel_errors.py`)
   - `ExcelError`: Base error class with context information
   - `ValidationError`: Data validation errors
   - `FormatError`: Format-related errors
   - `DuplicateError`: Duplicate record errors
   - `RequiredFieldError`: Missing required fields
   - `ReferenceError`: Invalid references (categories, products, etc.)
   - `DataTypeError`: Wrong data type errors
   - `RangeError`: Value out of range errors
   - `FileError`: File-level errors
   - `ErrorCollector`: Collects and manages errors/warnings

2. **Validators**
   - `products/excel_validators.py`: Product Excel validation
   - `orders/excel_validators.py`: Order Excel validation

3. **Error Display Component**
   - `templates/components/excel_errors.html`: Reusable error display

## Features

### 1. Detailed Error Information

Each error includes:
- Error code (for categorization)
- Turkish error message
- Row number
- Column name
- Field name
- Invalid value
- Suggestion for fixing
- Additional context

### 2. Error Categories

- **Validation Errors**: Data doesn't meet business rules
- **Format Errors**: Incorrect data format
- **Duplicate Errors**: Duplicate SKUs or records
- **Reference Errors**: Invalid category/product references
- **Required Field Errors**: Missing mandatory data
- **Data Type Errors**: Wrong data types
- **Range Errors**: Values outside acceptable range
- **File Errors**: File-level issues

### 3. Turkish Language Support

All error messages and suggestions are in Turkish:
```python
ERROR_MESSAGES = {
    'INVALID_SKU_FORMAT': 'SKU formatı geçersiz. SKU en az 3 karakter olmalı ve özel karakterler içermemelidir.',
    'DUPLICATE_SKU': 'Bu SKU zaten kullanılıyor',
    'INVALID_PRICE': 'Geçersiz fiyat formatı. Fiyat pozitif bir sayı olmalıdır',
    # ... more messages
}
```

### 4. Error Display UI

The error display component shows:
- Error summary with counts
- Categorized error breakdown
- Detailed error table
- Warnings section
- Export to Excel functionality

### 5. Error Export

Users can export error reports as Excel files for offline review and correction.

## Usage

### 1. In Views

```python
from core.excel_errors import ErrorCollector
from products.excel_validators import ProductExcelValidator

def import_products(request):
    # Read Excel file
    df = pd.read_excel(file_obj)
    
    # Initialize validator
    validator = ProductExcelValidator()
    
    # Validate file
    if not validator.validate_file(df):
        context = {
            'errors': validator.error_collector.to_list(),
            'error_summary': validator.error_collector.get_summary()
        }
        return render(request, 'template.html', context)
    
    # Validate rows
    for index, row in df.iterrows():
        cleaned_data = validator.validate_row(row.to_dict(), index + 2)
        # Process cleaned data...
```

### 2. In Templates

```django
{% if errors %}
    {% include 'components/excel_errors.html' %}
{% endif %}
```

### 3. Custom Validators

Create custom validators by extending base validator:

```python
class ProductExcelValidator:
    def validate_row(self, row_data, row_number):
        # SKU validation
        sku = self._validate_sku(row_data.get('sku'), row_number)
        
        # Price validation
        price = self._validate_price(row_data.get('price'), row_number)
        
        # Return cleaned data
        return {'sku': sku, 'price': price}
```

## Error Types and Messages

### Product Import Errors

1. **SKU Errors**
   - Too short: "SKU en az 3 karakter olmalıdır"
   - Invalid format: "SKU sadece harf, rakam, tire, alt çizgi ve nokta içerebilir"
   - Duplicate: "Bu SKU zaten kullanılıyor"

2. **Price Errors**
   - Invalid format: "Geçersiz fiyat formatı"
   - Negative value: "Fiyat 0'dan büyük olmalıdır"
   - Too large: "Fiyat en fazla 999,999.99 olabilir"

3. **Category Errors**
   - Not found: "'Category Name' kategorisi mevcut değil"
   - Suggestion shows available categories

### Order Import Errors

1. **Customer Errors**
   - Invalid email: "Geçersiz e-posta adresi"
   - Invalid phone: "Geçersiz telefon numarası"
   - Customer not found (can create new)

2. **Date Errors**
   - Invalid format: "Geçersiz tarih formatı"
   - Future date: "Sipariş tarihi gelecekte olamaz"

3. **Product Errors**
   - Product not found: "'SKU' SKU numaralı ürün bulunamadı"

4. **Quantity/Price Errors**
   - Invalid quantity: "Miktar pozitif bir tam sayı olmalıdır"
   - Invalid discount: "İndirim 0-100 arasında olmalıdır"

## Testing

Run tests with:
```bash
python manage.py test products.tests.test_excel_errors
```

## Best Practices

1. **Always validate before processing**
   - File-level validation first
   - Row-by-row validation
   - Show all errors at once

2. **Provide helpful suggestions**
   - Include format examples
   - Show available options
   - Explain how to fix

3. **Use appropriate error types**
   - Choose correct error class
   - Provide context information
   - Include row/column details

4. **Handle large files gracefully**
   - Process in chunks if needed
   - Show progress indicators
   - Limit error display count

## Future Improvements

1. **Async Processing**: Handle large files asynchronously
2. **Progress Tracking**: Show import progress in real-time
3. **Auto-correction**: Suggest and apply automatic fixes
4. **Template Generation**: Include example data in templates
5. **Validation Rules Config**: Make validation rules configurable