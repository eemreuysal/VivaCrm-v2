# Excel Import Error Correction System Example

## Overview
VivaCRM v2 now includes an intelligent error correction system for Excel imports that can automatically detect and fix common data issues.

## Features

### 1. Error Classification
- **Correctable Errors**: Issues that can be automatically or manually fixed
  - Price format errors (comma vs dot)
  - Date format variations
  - SKU formatting issues
  - Category name matching
  - Stock quantity validation

- **Non-Correctable Errors**: Critical issues that prevent import
  - Missing required fields
  - Duplicate SKUs (if not updating)
  - Invalid tax rates
  - System errors

### 2. Automatic Corrections

The system can automatically fix:
- **Price Format**: Converts "10,50" to "10.50", removes currency symbols
- **Date Format**: Handles various formats (DD/MM/YYYY, MM/DD/YYYY, etc.)
- **SKU Format**: Removes spaces, special characters, standardizes format
- **Category Matching**: Finds similar category names using fuzzy matching
- **Stock Values**: Converts negative values to 0, cleans numeric formats

### 3. Interactive Correction Interface

When errors are detected:
1. Summary shows total errors, correctable errors, and auto-correctable errors
2. Automatic correction options are presented with checkboxes
3. Manual correction form allows editing individual values
4. Real-time preview of corrections
5. Ability to skip specific errors

### 4. Import Flow

1. **Upload Excel File**
   ```
   products/excel/import/
   ```

2. **Validation Phase**
   - File structure validation
   - Required columns check
   - Data type validation
   - Business rule validation

3. **Error Correction**
   - If errors found, redirect to correction interface
   - Apply automatic corrections
   - Manually fix remaining issues
   - Option to skip non-critical errors

4. **Processing**
   - After corrections, continue with import
   - Create new products or update existing
   - Show success summary

## Usage Example

### Excel File Format
```
SKU         | Ürün Adı    | Fiyat  | Kategori      | Stok
------------|-------------|--------|---------------|------
PROD-001    | Ürün 1      | 10,50  | Elektronik    | 100
PROD-002    | Ürün 2      | 25.00  | Giyim         | 50
PROD 003    | Ürün 3      | 15,75  | Elektrnik     | -5
```

### Error Detection
- PROD-001: Price format error (comma)
- PROD 003: SKU format error (space)
- PROD 003: Category not found (typo)
- PROD 003: Invalid stock value (negative)

### Automatic Corrections
- Price: "10,50" → "10.50"
- SKU: "PROD 003" → "PROD_003"
- Category: "Elektrnik" → "Elektronik" (fuzzy match)
- Stock: "-5" → "0"

## API Endpoints

1. **Import Products**
   ```
   POST /products/excel/import/
   ```

2. **Apply Corrections**
   ```
   POST /products/excel/apply-corrections/
   ```

## Technical Implementation

### Key Components
1. `core/excel_errors.py`: Error classification system
2. `core/excel_corrections.py`: Automatic correction logic
3. `templates/components/error_correction_form.html`: UI component
4. `products/views_excel.py`: Import and correction views

### Correction Rules
```python
# Example correction rules
correction_rules = {
    'price': 'price',      # Price format correction
    'sku': 'sku',         # SKU standardization
    'category': 'category', # Category matching
    'stock_quantity': 'stock'  # Stock validation
}
```

### Cache-Based Session Management
- Import sessions stored in cache
- 1-hour timeout for correction process
- DataFrame preserved between correction steps

## Benefits
1. Reduced manual data cleaning effort
2. Intelligent error suggestions
3. Batch corrections for similar issues
4. Category fuzzy matching prevents typos
5. Preserves data integrity
6. User-friendly correction interface