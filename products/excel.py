"""
Excel import/export functionality for the Products app.
"""
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import transaction
import pandas as pd
from datetime import datetime
import decimal
import logging
from typing import Dict, Any, Optional, List, Union

from core.excel import ExcelExporter, ExcelImporter, generate_template_excel
from .models import Product, Category, StockMovement

logger = logging.getLogger(__name__)


# Field definitions for Product exports
PRODUCT_EXPORT_FIELDS = [
    'id', 'code', 'name', 'category__name', 'price', 'cost', 'tax_rate',
    'sale_price', 'sale_end_date', 'current_stock', 'threshold_stock',
    'is_physical', 'weight', 'dimensions', 'sku', 'barcode', 'status', 
    'description'
]

PRODUCT_EXPORT_HEADERS = {
    'id': 'ID',
    'code': 'Product Code',
    'name': 'Product Name',
    'category__name': 'Category',
    'price': 'Price',
    'cost': 'Cost',
    'tax_rate': 'Tax Rate (%)',
    'sale_price': 'Sale Price',
    'sale_end_date': 'Sale End Date',
    'current_stock': 'Current Stock',
    'threshold_stock': 'Threshold Stock',
    'is_physical': 'Physical Product',
    'weight': 'Weight (kg)',
    'dimensions': 'Dimensions',
    'sku': 'SKU',
    'barcode': 'Barcode',
    'status': 'Status',
    'description': 'Description'
}


def export_products_excel(queryset, filename=None):
    """
    Export products to Excel format.
    """
    if filename is None:
        filename = f"products_export_{timezone.now().strftime('%Y%m%d_%H%M')}"
    
    exporter = ExcelExporter(
        queryset=queryset,
        fields=PRODUCT_EXPORT_FIELDS,
        headers=PRODUCT_EXPORT_HEADERS,
        filename=filename,
        sheet_name='Products'
    )
    return exporter.to_excel()


def export_products_csv(queryset, filename=None):
    """
    Export products to CSV format.
    """
    if filename is None:
        filename = f"products_export_{timezone.now().strftime('%Y%m%d_%H%M')}"
    
    exporter = ExcelExporter(
        queryset=queryset,
        fields=PRODUCT_EXPORT_FIELDS,
        headers=PRODUCT_EXPORT_HEADERS,
        filename=filename
    )
    return exporter.to_csv()


def generate_product_import_template():
    """
    Generate an Excel template for importing products.
    """
    headers = {
        'code': 'Product Code *',
        'name': 'Product Name *',
        'category': 'Category *',
        'price': 'Price *',
        'cost': 'Cost',
        'tax_rate': 'Tax Rate (%)',
        'sale_price': 'Sale Price',
        'sale_end_date': 'Sale End Date (YYYY-MM-DD)',
        'current_stock': 'Initial Stock *',
        'threshold_stock': 'Stock Alert Threshold',
        'is_physical': 'Physical Product (TRUE/FALSE)',
        'weight': 'Weight (kg)',
        'dimensions': 'Dimensions',
        'sku': 'SKU',
        'barcode': 'Barcode',
        'status': 'Status (available/unavailable/coming_soon/discontinued)',
        'description': 'Description'
    }
    
    fields = list(headers.keys())
    
    return generate_template_excel(
        model=Product,
        fields=fields,
        headers=headers,
        filename='product_import_template'
    )


# Field validators and processors for import
def validate_category(category_name):
    """
    Validate and get or create a category by name.
    """
    if not category_name:
        raise ValidationError("Category is required")
    
    # Try to find or create the category
    category, created = Category.objects.get_or_create(name=category_name)
    return category


def validate_price(value):
    """
    Validate price/cost fields.
    """
    if value == '':
        return None
    
    try:
        return decimal.Decimal(str(value))
    except:
        raise ValidationError(f"Invalid price value: {value}")


def validate_date(value):
    """
    Validate and parse date strings.
    """
    if not value or value == '':
        return None
    
    try:
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        else:
            return None
    except:
        raise ValidationError(f"Invalid date format. Use YYYY-MM-DD: {value}")


def validate_boolean(value):
    """
    Validate and parse boolean values.
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value = value.lower()
        if value in ['true', 'yes', '1', 'y', 't']:
            return True
        elif value in ['false', 'no', '0', 'n', 'f']:
            return False
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    return False


def validate_status(value):
    """
    Validate product status.
    """
    if not value:
        return 'available'
    
    valid_statuses = ['available', 'unavailable', 'coming_soon', 'discontinued']
    
    if value.lower() in valid_statuses:
        return value.lower()
    
    raise ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")


def import_products_excel(file_obj, update_existing=True) -> Dict[str, Any]:
    """
    Import products from Excel file.
    
    Args:
        file_obj: File object containing Excel data
        update_existing: Whether to update existing products
        
    Returns:
        Dict with import statistics
    """
    # Define field mapping
    field_mapping = {
        'Product Code *': 'code',
        'Product Code': 'code',
        'Product Name *': 'name',
        'Product Name': 'name',
        'Category *': 'category',
        'Category': 'category',
        'Price *': 'price',
        'Price': 'price',
        'Cost': 'cost',
        'Tax Rate (%)': 'tax_rate',
        'Sale Price': 'sale_price',
        'Sale End Date (YYYY-MM-DD)': 'sale_end_date',
        'Sale End Date': 'sale_end_date',
        'Initial Stock *': 'current_stock',
        'Initial Stock': 'current_stock',
        'Current Stock': 'current_stock',
        'Stock Alert Threshold': 'threshold_stock',
        'Physical Product (TRUE/FALSE)': 'is_physical',
        'Physical Product': 'is_physical',
        'Weight (kg)': 'weight',
        'Dimensions': 'dimensions',
        'SKU': 'sku',
        'Barcode': 'barcode',
        'Status (available/unavailable/coming_soon/discontinued)': 'status',
        'Status': 'status',
        'Description': 'description'
    }
    
    # Define required fields
    required_fields = ['code', 'name', 'category', 'price', 'current_stock']
    
    # Define field validators
    validators = {
        'category': validate_category,
        'price': validate_price,
        'cost': validate_price,
        'sale_price': validate_price,
        'sale_end_date': validate_date,
        'is_physical': validate_boolean,
        'status': validate_status
    }
    
    # Initialize importer
    importer = ExcelImporter(
        model=Product,
        field_mapping=field_mapping,
        required_fields=required_fields,
        unique_fields=['code'],  # Unique field for update/create
        validators=validators
    )
    
    # Perform the import
    result = importer.import_data(file_obj, update_existing=update_existing)
    
    # Handle stock movements for new products
    if result['created'] > 0:
        _create_stock_movements_for_imports(file_obj)
    
    return result


def _create_stock_movements_for_imports(file_obj) -> None:
    """
    Create initial stock movements for imported products.
    """
    try:
        # Read the file again
        df = pd.read_excel(file_obj)
        
        # Map column names
        code_col = next((col for col in df.columns if 'product code' in col.lower()), None)
        stock_col = next((col for col in df.columns if 'stock' in col.lower()), None)
        
        if not code_col or not stock_col:
            logger.warning("Could not identify code and stock columns for stock movements")
            return
        
        # Create stock movements for products with positive stock
        movements = []
        for _, row in df.iterrows():
            code = row[code_col]
            stock = row[stock_col]
            
            # Skip if no code or stock is zero/nan
            if not code or pd.isna(stock) or stock <= 0:
                continue
            
            try:
                product = Product.objects.get(code=code)
                
                # Create stock movement
                movement = StockMovement(
                    product=product,
                    movement_type='initial',
                    quantity=int(stock),
                    reference='Initial import',
                    notes='Created during product import'
                )
                movements.append(movement)
                
            except Product.DoesNotExist:
                logger.warning(f"Product with code {code} not found for stock movement")
                continue
        
        # Bulk create all movements
        if movements:
            StockMovement.objects.bulk_create(movements)
            logger.info(f"Created {len(movements)} stock movements for imported products")
    
    except Exception as e:
        logger.error(f"Error creating stock movements for imports: {str(e)}")


# Field definitions for Stock export
STOCK_EXPORT_FIELDS = [
    'id', 'code', 'name', 'category__name', 'current_stock', 
    'threshold_stock', 'sku', 'status'
]

STOCK_EXPORT_HEADERS = {
    'id': 'ID',
    'code': 'Product Code',
    'name': 'Product Name',
    'category__name': 'Category',
    'current_stock': 'Current Stock',
    'threshold_stock': 'Threshold Stock',
    'sku': 'SKU',
    'status': 'Status'
}


def export_stock_excel(queryset, filename=None):
    """
    Export stock information to Excel.
    """
    if filename is None:
        filename = f"stock_export_{timezone.now().strftime('%Y%m%d_%H%M')}"
    
    exporter = ExcelExporter(
        queryset=queryset,
        fields=STOCK_EXPORT_FIELDS,
        headers=STOCK_EXPORT_HEADERS,
        filename=filename,
        sheet_name='Stock'
    )
    return exporter.to_excel()


def generate_stock_adjustment_template():
    """
    Generate an Excel template for bulk stock adjustments.
    """
    headers = {
        'code': 'Product Code *',
        'name': 'Product Name (Read Only)',
        'category': 'Category (Read Only)',
        'current_stock': 'Current Stock (Read Only)',
        'quantity': 'Adjustment Quantity *',
        'movement_type': 'Movement Type (in/out/adjust) *',
        'reference': 'Reference',
        'notes': 'Notes'
    }
    
    fields = list(headers.keys())
    
    return generate_template_excel(
        model=Product,
        fields=fields,
        headers=headers,
        filename='stock_adjustment_template'
    )


@transaction.atomic
def import_stock_adjustments(file_obj) -> Dict[str, Any]:
    """
    Import stock adjustments from Excel file.
    
    Args:
        file_obj: File object containing Excel data
        
    Returns:
        Dict with import statistics
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_obj)
        df = df.fillna('')
        
        # Validate required columns
        required_columns = ['Product Code *', 'Adjustment Quantity *', 'Movement Type (in/out/adjust) *']
        for column in required_columns:
            if column not in df.columns and column.replace(' *', '') not in df.columns:
                alt_name = column.replace(' *', '')
                if alt_name not in df.columns:
                    raise ValidationError(f"Missing required column: {column}")
        
        # Map columns
        code_col = next((col for col in df.columns if 'product code' in col.lower()), None)
        qty_col = next((col for col in df.columns if 'quantity' in col.lower()), None)
        type_col = next((col for col in df.columns if 'movement type' in col.lower()), None)
        ref_col = next((col for col in df.columns if 'reference' in col.lower()), None)
        notes_col = next((col for col in df.columns if 'notes' in col.lower()), None)
        
        # Process each row
        success_count = 0
        error_count = 0
        error_rows = []
        
        for index, row in df.iterrows():
            try:
                # Get required data
                code = row[code_col]
                quantity = row[qty_col]
                movement_type = str(row[type_col]).lower() if row[type_col] else 'adjust'
                
                # Validate movement type
                if movement_type not in ['in', 'out', 'adjust']:
                    raise ValidationError(f"Invalid movement type: {movement_type}. Must be 'in', 'out', or 'adjust'")
                
                # Validate quantity
                try:
                    quantity = int(quantity)
                    if movement_type == 'out':
                        quantity = -abs(quantity)  # Ensure negative for outgoing
                    elif movement_type == 'in':
                        quantity = abs(quantity)  # Ensure positive for incoming
                except:
                    raise ValidationError(f"Invalid quantity: {quantity}")
                
                # Get the product
                try:
                    product = Product.objects.get(code=code)
                except Product.DoesNotExist:
                    raise ValidationError(f"Product with code {code} does not exist")
                
                # Get optional fields
                reference = row[ref_col] if ref_col in row and row[ref_col] else 'Bulk adjustment'
                notes = row[notes_col] if notes_col in row and row[notes_col] else ''
                
                # Create the stock movement
                StockMovement.objects.create(
                    product=product,
                    movement_type=movement_type,
                    quantity=quantity,
                    reference=reference,
                    notes=notes
                )
                
                # Update the product stock
                if movement_type == 'adjust':
                    # Set stock directly to the new value
                    product.current_stock = quantity
                else:
                    # Adjust stock by the quantity
                    product.current_stock = product.current_stock + quantity
                
                product.save(update_fields=['current_stock'])
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing row {index + 2}: {str(e)}")
                error_count += 1
                error_rows.append({
                    'row': index + 2,
                    'data': row.to_dict(),
                    'error': str(e)
                })
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'error_rows': error_rows,
            'total': len(df)
        }
        
    except Exception as e:
        logger.error(f"Error importing stock adjustments: {str(e)}")
        raise ValidationError(f"Error importing stock adjustments: {str(e)}")