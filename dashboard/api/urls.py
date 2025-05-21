from django.urls import path
from .views import (
    dashboard_stats, dashboard_chart_data, DashboardApiView
)

app_name = 'dashboard_api'

urlpatterns = [
    path('summary/', dashboard_stats, name='summary'),
    path('chart/<str:chart_type>/', dashboard_chart_data, name='chart-data'),
    path('dashboard-data/', DashboardApiView.as_view(), name='dashboard-data'),
]