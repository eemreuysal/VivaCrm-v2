from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path("", views.AdminDashboardView.as_view(), name="dashboard"),
    path("users/", views.AdminUserListView.as_view(), name="user-list"),
    path("users/<str:username>/", views.AdminUserDetailView.as_view(), name="user-detail"),
    path("settings/", views.SystemSettingsView.as_view(), name="system-settings"),
    path("logs/", views.SystemLogsView.as_view(), name="system-logs"),
    path("backup/", views.BackupView.as_view(), name="backup"),
]