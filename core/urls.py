"""
URL configuration for VivaCRM v2 project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views.test_views import test_dashboard

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # API routes
    path("api/v1/", include("core.api_router")),
    path("api/", include("core.api.urls")),
    
    # App routes - will be uncommented as apps are created
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("customers/", include("customers.urls")),
    path("products/", include("products.urls")),
    path("orders/", include("orders.urls")),
    path("reports/", include("reports.urls")),
    path("invoices/", include("invoices.urls")),
    path("admin-panel/", include("admin_panel.urls")),
    
    # Core import history
    path("core/", include("core.urls_import", namespace="core")),
    
    # Core validation system  
    path("core/validation/", include("core.urls_validation", namespace="core_validation")),
    
    # Design System
    path("design-system/", TemplateView.as_view(template_name="design_system.html"), name="design-system"),
    
    # Test CSS
    path("test-css/", TemplateView.as_view(template_name="test_css.html"), name="test-css"),
    
    # Test Dashboard
    path("test-dashboard/", test_dashboard, name="test-dashboard"),
    
    # Alpine.js Test Pages
    path("test-alpine/", TemplateView.as_view(template_name="test_alpine.html"), name="test-alpine"),
    path("test-alpine-simple/", TemplateView.as_view(template_name="test_alpine_simple.html"), name="test-alpine-simple"),
    path("test-alpine-inline/", TemplateView.as_view(template_name="test_alpine_inline.html"), name="test-alpine-inline"),
    path("test-alpine-minimal/", TemplateView.as_view(template_name="test_alpine_minimal.html"), name="test-alpine-minimal"),
    path("test-alpine-store/", TemplateView.as_view(template_name="test_alpine_store.html"), name="test-alpine-store"),
    path("test-components/", TemplateView.as_view(template_name="test_components.html"), name="test-components"),
    
    # Redirect root URL to dashboard
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
]

# Static & Media in Development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug Toolbar
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]