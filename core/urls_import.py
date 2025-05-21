"""
Import history URL configuration
"""
from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Geçici bakım sayfası
@method_decorator(login_required, name='dispatch')
class MaintenanceView(TemplateView):
    template_name = "orders/maintenance.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Import Özelliği Bakımda"
        context['message'] = "Excel import özelliği şu anda bakımda, lütfen daha sonra tekrar deneyin."
        return context

app_name = 'core'

# Geçici olarak tüm importları bakım sayfasına yönlendir
urlpatterns = [
    path('import/', MaintenanceView.as_view(), name='import-history'),
    path('import/<int:pk>/', MaintenanceView.as_view(), name='import-history-detail'),
    path('import/<int:pk>/reload/', MaintenanceView.as_view(), name='import-reload'),
    path('import/<int:pk>/preview/', MaintenanceView.as_view(), name='import-file-preview'),
    path('import/<int:pk>/download/', MaintenanceView.as_view(), name='import-download'),
    path('import/<int:pk>/status/', MaintenanceView.as_view(), name='import-status'),
    path('import/stats/', MaintenanceView.as_view(), name='import-stats'),
]

# Orijinal import linklerini yorum satırına aldık
# from . import views_import
# urlpatterns = [
#     # Import history list
#     path('import/', views_import.ImportHistoryListView.as_view(), name='import-history'),
#     
#     # Import history detail
#     path('import/<int:pk>/', views_import.ImportHistoryDetailView.as_view(), name='import-history-detail'),
#     
#     # Import reload
#     path('import/<int:pk>/reload/', views_import.ImportReloadView.as_view(), name='import-reload'),
#     
#     # Import file preview
#     path('import/<int:pk>/preview/', views_import.import_file_preview, name='import-file-preview'),
#     
#     # Import download
#     path('import/<int:pk>/download/', views_import.import_download, name='import-download'),
#     
#     # Import status check
#     path('import/<int:pk>/status/', views_import.import_status_api, name='import-status'),
#     
#     # Import statistics API
#     path('import/stats/', views_import.import_stats_api, name='import-stats'),
# ]