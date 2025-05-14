from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, ProductImageViewSet,
    ProductAttributeViewSet, ProductAttributeValueViewSet,
    StockMovementViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'images', ProductImageViewSet)
router.register(r'attributes', ProductAttributeViewSet)
router.register(r'attribute-values', ProductAttributeValueViewSet)
router.register(r'stock-movements', StockMovementViewSet)

app_name = 'products_api'

urlpatterns = [
    path('', include(router.urls)),
]