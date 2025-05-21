from django.urls import path, include
from . import views
from .api.views import (
    DashboardApiView, 
    dashboard_stats, 
    dashboard_chart_data
)

app_name = 'dashboard'

# Temel URL'ler
urlpatterns = [
    # Ana dashboard sayfası - tam sayfa
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Dashboard içerik - kısmi güncelleme için
    path('content/', views.DashboardContentView.as_view(), name='dashboard-content'),
    
    # API endpoint'leri
    path('api/', include([
        path('stats/', dashboard_stats, name='api-stats'),
        path('chart/<str:chart_type>/', dashboard_chart_data, name='api-chart-data'),
        path('data/', DashboardApiView.as_view(), name='api-data'),
    ])),
]