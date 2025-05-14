"""
Data validation utilities for VivaCRM v2.

This module provides validation functions for various data types and models
to ensure data integrity throughout the application.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import validate_email as django_validate_email
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import re
from typing import Optional, Union, Any, Dict, List, Tuple
import logging
from core.security import (
    validate_email as security_validate_email,
    validate_phone, validate_tax_id, validate_url
)

logger = logging.getLogger(__name__)


def validate_model_integrity(model_instance, update_fields=None):
    """
    Perform thorough validation on a model instance to ensure data integrity.
    
    Args:
        model_instance: A Django model instance
        update_fields: Optional list of fields being updated
        
    Raises:
        ValidationError: If validation fails
    """
    # First run the model's own validation
    try:
        model_instance.full_clean(exclude=None)
    except ValidationError as e:
        raise e
    
    # Then get the model class
    model_class = model_instance.__class__
    
    # Check for any model-specific validation logic
    model_validator_name = f"validate_{model_class.__name__.lower()}"
    model_validator = globals().get(model_validator_name)
    if model_validator:
        model_validator(model_instance, update_fields)


def validate_positive_decimal(value, field_name="value"):
    """
    Validate that a value is a positive decimal.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Decimal: The validated decimal value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError({field_name: _("Must be a valid decimal number")})
    
    if decimal_value < 0:
        raise ValidationError({field_name: _("Must be a positive number")})
    
    return decimal_value


def validate_non_negative_decimal(value, field_name="value"):
    """
    Validate that a value is a non-negative decimal.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Decimal: The validated decimal value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError({field_name: _("Must be a valid decimal number")})
    
    if decimal_value < 0:
        raise ValidationError({field_name: _("Cannot be negative")})
    
    return decimal_value


def validate_percentage(value, field_name="percentage"):
    """
    Validate that a value is a valid percentage (0-100).
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Decimal: The validated percentage value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError({field_name: _("Must be a valid percentage")})
    
    if decimal_value < 0 or decimal_value > 100:
        raise ValidationError({field_name: _("Must be between 0 and 100")})
    
    return decimal_value


def validate_future_date(value, field_name="date"):
    """
    Validate that a date is in the future.
    
    Args:
        value: The date to validate
        field_name: Name of the field for error messages
        
    Returns:
        date: The validated date
        
    Raises:
        ValidationError: If validation fails
    """
    if not value:
        return None
    
    # Convert to date if it's a datetime
    if isinstance(value, datetime):
        value = value.date()
    
    if not isinstance(value, date):
        raise ValidationError({field_name: _("Must be a valid date")})
    
    if value < timezone.now().date():
        raise ValidationError({field_name: _("Must be a future date")})
    
    return value


def validate_past_date(value, field_name="date"):
    """
    Validate that a date is in the past.
    
    Args:
        value: The date to validate
        field_name: Name of the field for error messages
        
    Returns:
        date: The validated date
        
    Raises:
        ValidationError: If validation fails
    """
    if not value:
        return None
    
    # Convert to date if it's a datetime
    if isinstance(value, datetime):
        value = value.date()
    
    if not isinstance(value, date):
        raise ValidationError({field_name: _("Must be a valid date")})
    
    if value > timezone.now().date():
        raise ValidationError({field_name: _("Must be a past date")})
    
    return value


def validate_email(value, field_name="email"):
    """
    Validate an email address.
    
    Args:
        value: The email to validate
        field_name: Name of the field for error messages
        
    Returns:
        str: The validated email
        
    Raises:
        ValidationError: If validation fails
    """
    if not value:
        return None
    
    # Use Django's built-in validator
    try:
        django_validate_email(value)
    except ValidationError:
        raise ValidationError({field_name: _("Enter a valid email address")})
    
    # Additional validation from security module
    if not security_validate_email(value):
        raise ValidationError({field_name: _("Enter a valid email address")})
    
    return value


def validate_phone_number(value, field_name="phone"):
    """
    Validate a phone number.
    
    Args:
        value: The phone number to validate
        field_name: Name of the field for error messages
        
    Returns:
        str: The validated phone number
        
    Raises:
        ValidationError: If validation fails
    """
    if not value:
        return None
    
    if not validate_phone(value):
        raise ValidationError({field_name: _("Enter a valid phone number")})
    
    return value


def validate_tax_number(value, field_name="tax_number"):
    """
    Validate a Turkish tax number.
    
    Args:
        value: The tax number to validate
        field_name: Name of the field for error messages
        
    Returns:
        str: The validated tax number
        
    Raises:
        ValidationError: If validation fails
    """
    if not value:
        return None
    
    if not validate_tax_id(value):
        raise ValidationError({field_name: _("Enter a valid tax number")})
    
    return value


def validate_website(value, field_name="website"):
    """
    Validate a website URL.
    
    Args:
        value: The URL to validate
        field_name: Name of the field for error messages
        
    Returns:
        str: The validated URL
        
    Raises:
        ValidationError: If validation fails
    """
    if not value:
        return None
    
    if not validate_url(value):
        raise ValidationError({field_name: _("Enter a valid URL")})
    
    return value


def validate_positive_integer(value, field_name="value"):
    """
    Validate that a value is a positive integer.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        int: The validated integer value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError({field_name: _("Must be a valid integer")})
    
    if int_value <= 0:
        raise ValidationError({field_name: _("Must be a positive number")})
    
    return int_value


def validate_non_negative_integer(value, field_name="value"):
    """
    Validate that a value is a non-negative integer.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        int: The validated integer value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError({field_name: _("Must be a valid integer")})
    
    if int_value < 0:
        raise ValidationError({field_name: _("Cannot be negative")})
    
    return int_value


# Model-specific validation functions

def validate_order(order, update_fields=None):
    """
    Validate an Order model instance.
    
    Args:
        order: An Order model instance
        update_fields: Optional list of fields being updated
        
    Raises:
        ValidationError: If validation fails
    """
    errors = {}
    
    # Ensure order has at least one item
    if hasattr(order, 'items') and order.items.count() == 0:
        errors['items'] = _("An order must have at least one item")
    
    # Validate order dates
    if order.shipping_date and order.order_date and order.shipping_date < order.order_date:
        errors['shipping_date'] = _("Shipping date cannot be before order date")
    
    if order.delivery_date and order.shipping_date and order.delivery_date < order.shipping_date:
        errors['delivery_date'] = _("Delivery date cannot be before shipping date")
    
    # Validate totals
    if hasattr(order, 'calculate_totals'):
        calculated_total = order.calculate_totals(save=False)
        if abs(calculated_total - order.total_amount) > Decimal('0.01'):
            errors['total_amount'] = _("Total amount doesn't match calculated amount")
    
    if errors:
        raise ValidationError(errors)


def validate_invoice(invoice, update_fields=None):
    """
    Validate an Invoice model instance.
    
    Args:
        invoice: An Invoice model instance
        update_fields: Optional list of fields being updated
        
    Raises:
        ValidationError: If validation fails
    """
    errors = {}
    
    # Validate due date is after issue date
    if invoice.due_date and invoice.invoice_date and invoice.due_date < invoice.invoice_date:
        errors['due_date'] = _("Due date cannot be before invoice date")
    
    # Ensure invoice has at least one item
    if hasattr(invoice, 'items') and invoice.items.count() == 0:
        errors['items'] = _("An invoice must have at least one item")
    
    # Validate totals
    if hasattr(invoice, 'calculate_totals'):
        calculated_total = invoice.calculate_totals(save=False)
        if abs(calculated_total - invoice.total_amount) > Decimal('0.01'):
            errors['total_amount'] = _("Total amount doesn't match calculated amount")
    
    if errors:
        raise ValidationError(errors)


def validate_product(product, update_fields=None):
    """
    Validate a Product model instance.
    
    Args:
        product: A Product model instance
        update_fields: Optional list of fields being updated
        
    Raises:
        ValidationError: If validation fails
    """
    errors = {}
    
    # Validate pricing
    if product.sale_price is not None and product.price is not None:
        if product.sale_price >= product.price:
            errors['sale_price'] = _("Sale price must be lower than regular price")
    
    # Validate sale end date is in the future if sale price is set
    if product.sale_price is not None and product.sale_end_date is not None:
        if product.sale_end_date < timezone.now().date():
            errors['sale_end_date'] = _("Sale end date must be in the future")
    
    # Validate stock threshold logic
    if product.threshold_stock is not None and product.threshold_stock < 0:
        errors['threshold_stock'] = _("Stock threshold cannot be negative")
    
    if errors:
        raise ValidationError(errors)


def validate_payment(payment, update_fields=None):
    """
    Validate a Payment model instance.
    
    Args:
        payment: A Payment model instance
        update_fields: Optional list of fields being updated
        
    Raises:
        ValidationError: If validation fails
    """
    errors = {}
    
    # Validate payment amount is positive
    if payment.amount <= 0:
        errors['amount'] = _("Payment amount must be positive")
    
    # Validate payment date logic
    if payment.payment_date and payment.order and payment.order.order_date:
        if payment.payment_date < payment.order.order_date:
            errors['payment_date'] = _("Payment date cannot be before order date")
    
    if errors:
        raise ValidationError(errors)


def validate_customer(customer, update_fields=None):
    """
    Validate a Customer model instance.
    
    Args:
        customer: A Customer model instance
        update_fields: Optional list of fields being updated
        
    Raises:
        ValidationError: If validation fails
    """
    errors = {}
    
    # Validate required fields based on customer type
    if customer.type == 'corporate' and not customer.company_name:
        errors['company_name'] = _("Company name is required for corporate customers")
    
    # Validate tax information
    if customer.type == 'corporate' and not customer.tax_number:
        errors['tax_number'] = _("Tax number is required for corporate customers")
    
    if errors:
        raise ValidationError(errors)