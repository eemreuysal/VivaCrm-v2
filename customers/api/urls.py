from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, AddressViewSet, ContactViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'contacts', ContactViewSet)

app_name = 'customers_api'

urlpatterns = [
    path('', include(router.urls)),
]