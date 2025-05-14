from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Report Dashboard
    path("", views.ReportDashboardView.as_view(), name="dashboard"),
    
    # Report Types
    path("sales/", views.SalesReportView.as_view(), name="sales-report"),
    path("products/", views.ProductReportView.as_view(), name="product-report"),
    path("customers/", views.CustomerReportView.as_view(), name="customer-report"),
    
    # Saved Reports
    path("saved/", views.SavedReportListView.as_view(), name="saved-report-list"),
    path("saved/<int:pk>/", views.SavedReportDetailView.as_view(), name="saved-report-detail"),
    path("saved/<int:pk>/delete/", views.SavedReportDeleteView.as_view(), name="saved-report-delete"),
    path("save/", views.SaveReportView.as_view(), name="save-report"),
]