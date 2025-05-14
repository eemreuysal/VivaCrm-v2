"""
API router for VivaCRM v2 project.
"""

from django.urls import path, include

app_name = "api_v1"

urlpatterns = [
    # API endpoints
    path("accounts/", include("accounts.api.urls")),
    path("customers/", include("customers.api.urls")),
    path("products/", include("products.api.urls")),  
    path("orders/", include("orders.api.urls")),
    path("invoices/", include("invoices.api.urls")),
    path("dashboard/", include("dashboard.api.urls")),
    path("reports/", include("reports.api.urls")),
    path("admin/", include("admin_panel.api.urls")),
]