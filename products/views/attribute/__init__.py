"""
Product attribute views for the products app.
"""
from .views import (
    ProductAttributeListView,
    ProductAttributeCreateView,
    ProductAttributeUpdateView,
    ProductAttributeDeleteView,
    ProductAttributeValueCreateView,
    ProductAttributeValueUpdateView,
    ProductAttributeValueDeleteView,
)

__all__ = [
    'ProductAttributeListView',
    'ProductAttributeCreateView',
    'ProductAttributeUpdateView',
    'ProductAttributeDeleteView',
    'ProductAttributeValueCreateView',
    'ProductAttributeValueUpdateView',
    'ProductAttributeValueDeleteView',
]