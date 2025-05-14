from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet, PaymentViewSet, ShipmentViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'items', OrderItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'shipments', ShipmentViewSet)

app_name = 'orders_api'

urlpatterns = [
    path('', include(router.urls)),
]