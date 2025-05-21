"""
Product views for the products app.
"""
from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

__all__ = [
    'ProductListView',
    'ProductDetailView',
    'ProductCreateView',
    'ProductUpdateView',
    'ProductDeleteView',
]