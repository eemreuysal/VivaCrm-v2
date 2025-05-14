from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, InvoiceItemViewSet

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet)
router.register(r'items', InvoiceItemViewSet)

app_name = 'invoices_api'

urlpatterns = [
    path('', include(router.urls)),
]