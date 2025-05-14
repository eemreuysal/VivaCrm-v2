"""
Excel import/export functionality for the Customers app.
"""
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import transaction
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Union

from core.excel import ExcelExporter, ExcelImporter, generate_template_excel
from .models import Customer, Address, Contact

logger = logging.getLogger(__name__)


# Field definitions for Customer exports
CUSTOMER_EXPORT_FIELDS = [
    'id', 'name', 'type', 'company_name', 'tax_office', 'tax_number',
    'email', 'phone', 'website', 'owner__username', 'is_active',
    'created_at', 'notes'
]

CUSTOMER_EXPORT_HEADERS = {
    'id': 'ID',
    'name': 'Customer Name',
    'type': 'Type',
    'company_name': 'Company Name',
    'tax_office': 'Tax Office',
    'tax_number': 'Tax/ID Number',
    'email': 'Email',
    'phone': 'Phone',
    'website': 'Website',
    'owner__username': 'Owner',
    'is_active': 'Active',
    'created_at': 'Created At',
    'notes': 'Notes'
}


def export_customers_excel(queryset, filename=None):
    """
    Export customers to Excel format.
    """
    if filename is None:
        filename = f"customers_export_{timezone.now().strftime('%Y%m%d_%H%M')}"
    
    exporter = ExcelExporter(
        queryset=queryset,
        fields=CUSTOMER_EXPORT_FIELDS,
        headers=CUSTOMER_EXPORT_HEADERS,
        filename=filename,
        sheet_name='Customers'
    )
    return exporter.to_excel()


def export_customers_csv(queryset, filename=None):
    """
    Export customers to CSV format.
    """
    if filename is None:
        filename = f"customers_export_{timezone.now().strftime('%Y%m%d_%H%M')}"
    
    exporter = ExcelExporter(
        queryset=queryset,
        fields=CUSTOMER_EXPORT_FIELDS,
        headers=CUSTOMER_EXPORT_HEADERS,
        filename=filename
    )
    return exporter.to_csv()


def generate_customer_import_template():
    """
    Generate an Excel template for importing customers.
    """
    headers = {
        'name': 'Customer Name *',
        'type': 'Type (individual/corporate) *',
        'company_name': 'Company Name',
        'tax_office': 'Tax Office',
        'tax_number': 'Tax/ID Number',
        'email': 'Email *',
        'phone': 'Phone *',
        'website': 'Website',
        'notes': 'Notes'
    }
    
    fields = list(headers.keys())
    
    return generate_template_excel(
        model=Customer,
        fields=fields,
        headers=headers,
        filename='customer_import_template'
    )


# Field validators and processors for import
def validate_customer_type(value):
    """
    Validate customer type.
    """
    if not value:
        return 'individual'
    
    valid_types = ['individual', 'corporate']
    
    if value.lower() in valid_types:
        return value.lower()
    
    # Try to map common values
    if value.lower() in ['person', 'personal', 'private', 'bireysel']:
        return 'individual'
    if value.lower() in ['company', 'business', 'corp', 'kurumsal', 'şirket']:
        return 'corporate'
    
    raise ValidationError(f"Invalid customer type. Must be one of: {', '.join(valid_types)}")


def import_customers_excel(file_obj, update_existing=True) -> Dict[str, Any]:
    """
    Import customers from Excel file.
    
    Args:
        file_obj: File object containing Excel data
        update_existing: Whether to update existing customers
        
    Returns:
        Dict with import statistics
    """
    # Define field mapping
    field_mapping = {
        'Customer Name *': 'name',
        'Customer Name': 'name',
        'Type (individual/corporate) *': 'type',
        'Type': 'type',
        'Company Name': 'company_name',
        'Tax Office': 'tax_office',
        'Tax/ID Number': 'tax_number',
        'Email *': 'email',
        'Email': 'email',
        'Phone *': 'phone',
        'Phone': 'phone',
        'Website': 'website',
        'Notes': 'notes'
    }
    
    # Define required fields
    required_fields = ['name', 'type', 'email', 'phone']
    
    # Define field validators
    validators = {
        'type': validate_customer_type,
    }
    
    # Initialize importer
    importer = ExcelImporter(
        model=Customer,
        field_mapping=field_mapping,
        required_fields=required_fields,
        unique_fields=['email', 'phone'],  # Unique fields for update/create
        validators=validators,
        defaults={'is_active': True}
    )
    
    # Perform the import
    result = importer.import_data(file_obj, update_existing=update_existing)
    
    return result


# Field definitions for Address exports
ADDRESS_EXPORT_FIELDS = [
    'id', 'customer__name', 'title', 'type', 'address_line1', 'address_line2',
    'city', 'state', 'postal_code', 'country', 'is_default'
]

ADDRESS_EXPORT_HEADERS = {
    'id': 'ID',
    'customer__name': 'Customer',
    'title': 'Address Title',
    'type': 'Address Type',
    'address_line1': 'Address Line 1',
    'address_line2': 'Address Line 2',
    'city': 'City',
    'state': 'State/District',
    'postal_code': 'Postal Code',
    'country': 'Country',
    'is_default': 'Default Address'
}


def export_addresses_excel(queryset, filename=None):
    """
    Export customer addresses to Excel format.
    """
    if filename is None:
        filename = f"customer_addresses_export_{timezone.now().strftime('%Y%m%d_%H%M')}"
    
    exporter = ExcelExporter(
        queryset=queryset,
        fields=ADDRESS_EXPORT_FIELDS,
        headers=ADDRESS_EXPORT_HEADERS,
        filename=filename,
        sheet_name='Customer Addresses'
    )
    return exporter.to_excel()


def generate_address_import_template():
    """
    Generate an Excel template for importing customer addresses.
    """
    headers = {
        'customer_email': 'Customer Email *',
        'title': 'Address Title *',
        'type': 'Address Type (billing/shipping/other) *',
        'address_line1': 'Address Line 1 *',
        'address_line2': 'Address Line 2',
        'city': 'City *',
        'state': 'State/District',
        'postal_code': 'Postal Code',
        'country': 'Country',
        'is_default': 'Default Address (TRUE/FALSE)'
    }
    
    fields = list(headers.keys())
    
    return generate_template_excel(
        model=Address,
        fields=fields,
        headers=headers,
        filename='address_import_template'
    )


def validate_address_type(value):
    """
    Validate address type.
    """
    if not value:
        return 'other'
    
    valid_types = ['billing', 'shipping', 'other']
    
    if value.lower() in valid_types:
        return value.lower()
    
    # Try to map common values
    if value.lower() in ['bill', 'invoice', 'fatura']:
        return 'billing'
    if value.lower() in ['ship', 'delivery', 'sevkiyat', 'teslimat']:
        return 'shipping'
    
    raise ValidationError(f"Invalid address type. Must be one of: {', '.join(valid_types)}")


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


@transaction.atomic
def import_addresses_excel(file_obj, update_existing=True) -> Dict[str, Any]:
    """
    Import customer addresses from Excel file.
    
    Args:
        file_obj: File object containing Excel data
        update_existing: Whether to update existing addresses
        
    Returns:
        Dict with import statistics
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_obj)
        df = df.fillna('')
        
        # Track import statistics
        created_count = 0
        updated_count = 0
        error_count = 0
        error_rows = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Get customer email (required)
                customer_email = row.get('Customer Email *') or row.get('Customer Email')
                if not customer_email:
                    raise ValidationError("Customer Email is required")
                
                # Find the customer
                try:
                    customer = Customer.objects.get(email=customer_email)
                except Customer.DoesNotExist:
                    raise ValidationError(f"Customer with email {customer_email} does not exist")
                
                # Get address data
                title = row.get('Address Title *') or row.get('Address Title')
                if not title:
                    raise ValidationError("Address Title is required")
                
                address_type = validate_address_type(row.get('Address Type *') or row.get('Address Type', ''))
                
                address_line1 = row.get('Address Line 1 *') or row.get('Address Line 1')
                if not address_line1:
                    raise ValidationError("Address Line 1 is required")
                
                city = row.get('City *') or row.get('City')
                if not city:
                    raise ValidationError("City is required")
                
                # Optional fields
                address_line2 = row.get('Address Line 2', '')
                state = row.get('State/District', '')
                postal_code = row.get('Postal Code', '')
                country = row.get('Country', 'Türkiye')
                is_default = validate_boolean(row.get('Default Address', False))
                
                # Check if address exists
                address = None
                if update_existing:
                    try:
                        address = Address.objects.get(
                            customer=customer,
                            title=title
                        )
                    except Address.DoesNotExist:
                        pass
                
                if address:
                    # Update existing address
                    address.type = address_type
                    address.address_line1 = address_line1
                    address.address_line2 = address_line2
                    address.city = city
                    address.state = state
                    address.postal_code = postal_code
                    address.country = country
                    address.is_default = is_default
                    address.save()
                    updated_count += 1
                else:
                    # Create new address
                    Address.objects.create(
                        customer=customer,
                        title=title,
                        type=address_type,
                        address_line1=address_line1,
                        address_line2=address_line2,
                        city=city,
                        state=state,
                        postal_code=postal_code,
                        country=country,
                        is_default=is_default
                    )
                    created_count += 1
                
            except Exception as e:
                logger.error(f"Error importing address row {index + 2}: {str(e)}")
                error_count += 1
                error_rows.append({
                    'row': index + 2,  # Excel row number (1-based, plus header)
                    'data': row.to_dict(),
                    'error': str(e)
                })
        
        return {
            'created': created_count,
            'updated': updated_count,
            'error_count': error_count,
            'error_rows': error_rows,
            'total': len(df)
        }
        
    except Exception as e:
        logger.error(f"Error importing addresses file: {str(e)}")
        raise ValidationError(f"Error importing addresses file: {str(e)}")