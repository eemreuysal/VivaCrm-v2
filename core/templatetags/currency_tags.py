"""
Template tags for currency formatting.
"""
from django import template
from admin_panel.models import SystemSettings

register = template.Library()

@register.filter(name='currency')
def currency(value, include_symbol=True):
    """
    Format a value as currency.
    
    Args:
        value: The numeric value to format
        include_symbol: Whether to include the currency symbol
        
    Returns:
        Formatted currency string
    """
    try:
        # Try to convert value to float if it's not already numeric
        if not isinstance(value, (int, float, complex)):
            value = float(value)
        
        # Format with two decimal places
        formatted_value = "{:,.2f}".format(value)
        
        # Add currency symbol if requested
        if include_symbol:
            # Default currency symbols
            currency_symbols = {
                'TRY': '₺',
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
            }
            
            # Get currency from settings or default to USD
            currency = SystemSettings.get_setting('currency_code', 'USD')
            symbol = currency_symbols.get(currency, '$')
                
            return f"{formatted_value} {symbol}"
        
        return formatted_value
    except (ValueError, TypeError):
        return value  # Return original value if conversion fails

@register.simple_tag(name='get_currency_symbol')
def get_currency_symbol():
    """
    Get the current currency symbol based on system settings.
    
    Returns:
        The currency symbol as a string
    """
    # Default currency symbols
    currency_symbols = {
        'TRY': '₺',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
    }
    
    # Get currency from settings or default to USD
    currency = SystemSettings.get_setting('currency_code', 'USD')
    return currency_symbols.get(currency, '$')