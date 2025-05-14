from django.urls import path
from .views import (
    admin_dashboard, system_status, SystemLogsView, BackupView,
    RestoreView, SystemSettingsView, UserActivityView
)

app_name = 'admin_panel_api'

urlpatterns = [
    path('dashboard/', admin_dashboard, name='dashboard'),
    path('system/status/', system_status, name='system-status'),
    path('system/logs/', SystemLogsView.as_view(), name='system-logs'),
    path('system/backup/', BackupView.as_view(), name='backup'),
    path('system/restore/', RestoreView.as_view(), name='restore'),
    path('system/settings/', SystemSettingsView.as_view(), name='system-settings'),
    path('user-activity/', UserActivityView.as_view(), name='user-activity'),
]