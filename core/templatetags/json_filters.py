"""
JSON template filters for safe serialization.
"""
import json
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='json_safe')
def json_safe(value):
    """
    Convert a Python value to JSON and mark it as safe for direct inclusion in JavaScript.
    Uses DjangoJSONEncoder to handle Django-specific objects like datetime, Decimal, etc.
    """
    try:
        return mark_safe(json.dumps(value, cls=DjangoJSONEncoder))
    except (TypeError, ValueError) as e:
        # If serialization fails, return empty array
        return mark_safe('[]')