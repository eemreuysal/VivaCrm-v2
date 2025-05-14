from django.urls import path
from .views import (
    dashboard_summary, recent_orders, top_customers, top_products, 
    low_stock_products, SalesChartView, ProductCategoryChartView,
    OrderStatusChartView, CustomerTypeChartView
)

app_name = 'dashboard_api'

urlpatterns = [
    path('summary/', dashboard_summary, name='summary'),
    path('recent-orders/', recent_orders, name='recent-orders'),
    path('top-customers/', top_customers, name='top-customers'),
    path('top-products/', top_products, name='top-products'),
    path('low-stock-products/', low_stock_products, name='low-stock-products'),
    path('sales-chart/', SalesChartView.as_view(), name='sales-chart'),
    path('product-categories-chart/', ProductCategoryChartView.as_view(), name='product-categories-chart'),
    path('order-status-chart/', OrderStatusChartView.as_view(), name='order-status-chart'),
    path('customer-type-chart/', CustomerTypeChartView.as_view(), name='customer-type-chart'),
]