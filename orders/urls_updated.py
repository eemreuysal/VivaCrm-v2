"""
Orders modülü için URL yapılandırması.
Clean code prensipleriyle yeniden düzenlendi.
"""
from django.urls import path

from . import views
from .views import excel

# Ana URL'ler
urlpatterns = [
    # Sipariş listeleme ve detay sayfaları
    path('', views.OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/update/', views.OrderUpdateView.as_view(), name='order-update'),
    path('<int:pk>/delete/', views.OrderDeleteView.as_view(), name='order-delete'),
    
    # Sipariş durumları ve işlemleri
    path('<int:pk>/change-status/', views.change_order_status, name='change-order-status'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel-order'),
    path('<int:pk>/mark-as-paid/', views.mark_order_as_paid, name='mark-order-as-paid'),
    path('<int:pk>/mark-as-shipped/', views.mark_order_as_shipped, name='mark-order-as-shipped'),
    path('<int:pk>/mark-as-delivered/', views.mark_order_as_delivered, name='mark-order-as-delivered'),
    
    # Sipariş kalemleri
    path('<int:order_id>/items/add/', views.add_order_item, name='add-order-item'),
    path('items/<int:pk>/update/', views.update_order_item, name='update-order-item'),
    path('items/<int:pk>/delete/', views.delete_order_item, name='delete-order-item'),
    
    # Ödemeler
    path('<int:order_id>/payments/add/', views.add_payment, name='add-payment'),
    path('payments/<int:pk>/update/', views.update_payment, name='update-payment'),
    path('payments/<int:pk>/delete/', views.delete_payment, name='delete-payment'),
    
    # Kargolar
    path('<int:order_id>/shipments/add/', views.add_shipment, name='add-shipment'),
    path('shipments/<int:pk>/update/', views.update_shipment, name='update-shipment'),
    path('shipments/<int:pk>/delete/', views.delete_shipment, name='delete-shipment'),
    
    # Dashboard ve raporlama
    path('dashboard/', views.order_dashboard, name='order-dashboard'),
    path('reports/', views.order_reports, name='order-reports'),
    
    # API
    path('api/count-by-status/', views.count_orders_by_status, name='api-count-by-status'),
    path('api/monthly-totals/', views.get_monthly_order_totals, name='api-monthly-totals'),
]

# Excel işlemleri için URL'ler
excel_urlpatterns = [
    # Excel import
    path('excel/import/', excel.OrderExcelImportView.as_view(), name='excel-import'),
    path('excel/import/results/<str:session_id>/', excel.OrderExcelImportResultsView.as_view(), name='excel-import-results'),
    path('excel/import/template/', excel.OrderExcelTemplateView.as_view(), name='excel-template'),
    path('excel/validate/', excel.validate_excel_file, name='excel-validate'),
    
    # Excel export ve raporlar
    path('excel/report/', excel.OrderExcelReportView.as_view(), name='excel-report'),
]

# Tüm URL'leri birleştir
urlpatterns += excel_urlpatterns