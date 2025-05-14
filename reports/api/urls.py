from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SavedReportViewSet, SalesReportView, InventoryReportView,
    CustomerReportView, save_report
)

router = DefaultRouter()
router.register(r'saved-reports', SavedReportViewSet)

app_name = 'reports_api'

urlpatterns = [
    path('', include(router.urls)),
    path('sales/', SalesReportView.as_view(), name='sales-report'),
    path('inventory/', InventoryReportView.as_view(), name='inventory-report'),
    path('customers/', CustomerReportView.as_view(), name='customer-report'),
    path('save/', save_report, name='save-report'),
]