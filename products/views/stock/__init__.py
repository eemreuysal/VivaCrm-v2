"""
Stock management views for the products app.
"""
from .views import (
    StockMovementListView,
    StockMovementCreateView,
    StockMovementDetailView,
    BulkStockAdjustmentView,
    movement_fields_view,
)

__all__ = [
    'StockMovementListView',
    'StockMovementCreateView',
    'StockMovementDetailView',
    'BulkStockAdjustmentView',
    'movement_fields_view',
]