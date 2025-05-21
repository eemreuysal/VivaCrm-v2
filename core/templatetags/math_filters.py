from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def percentage(numerator, denominator):
    """Calculate percentage (numerator/denominator * 100)."""
    try:
        numerator = float(numerator or 0)
        denominator = float(denominator or 0)
        if denominator == 0:
            return 0
        return round((numerator / denominator) * 100, 2)
    except (ValueError, TypeError):
        return 0


@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide the value by the argument."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='abs_value')
def abs_value(value):
    """Return absolute value."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter(name='intcomma')
def intcomma(value):
    """Format a number with thousand separators."""
    try:
        # Convert to float first, then to int for integer formatting
        val = float(value)
        if val.is_integer():
            val = int(val)
        return "{:,}".format(val)
    except (ValueError, TypeError):
        return value