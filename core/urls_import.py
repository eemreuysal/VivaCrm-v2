"""
Import history URL configuration
"""
from django.urls import path
from . import views_import

app_name = 'core_import'

urlpatterns = [
    # Import history list
    path('import/', views_import.ImportHistoryListView.as_view(), name='import-history'),
    
    # Import history detail
    path('import/<int:pk>/', views_import.ImportHistoryDetailView.as_view(), name='import-history-detail'),
    
    # Import reload
    path('import/<int:pk>/reload/', views_import.ImportReloadView.as_view(), name='import-reload'),
    
    # Import file preview
    path('import/<int:pk>/preview/', views_import.import_file_preview, name='import-file-preview'),
    
    # Import download
    path('import/<int:pk>/download/', views_import.import_download, name='import-download'),
    
    # Import status check
    path('import/<int:pk>/status/', views_import.import_status_api, name='import-status'),
    
    # Import statistics API
    path('import/stats/', views_import.import_stats_api, name='import-stats'),
]