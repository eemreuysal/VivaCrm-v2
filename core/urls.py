"""
URL configuration for VivaCRM v2 project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # API routes
    path("api/v1/", include("core.api_router")),
    
    # App routes - will be uncommented as apps are created
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("customers/", include("customers.urls")),
    path("products/", include("products.urls")),
    path("orders/", include("orders.urls")),
    path("reports/", include("reports.urls")),
    path("invoices/", include("invoices.urls")),
    path("admin-panel/", include("admin_panel.urls")),
    
    # Design System
    path("design-system/", TemplateView.as_view(template_name="design_system.html"), name="design-system"),
    
    # Redirect root URL to dashboard
    path("", RedirectView.as_view(pattern_name="dashboard:dashboard"), name="home"),
]

# Static & Media in Development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug Toolbar
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]