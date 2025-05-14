from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # Order URLs
    path("", views.OrderListView.as_view(), name="order-list"),
    path("new/", views.OrderCreateView.as_view(), name="order-create"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/edit/", views.OrderUpdateView.as_view(), name="order-update"),
    path("<int:pk>/delete/", views.OrderDeleteView.as_view(), name="order-delete"),
    
    # OrderItem URLs
    path("<int:order_pk>/items/new/", views.OrderItemCreateView.as_view(), name="orderitem-create"),
    path("items/<int:pk>/edit/", views.OrderItemUpdateView.as_view(), name="orderitem-update"),
    path("items/<int:pk>/delete/", views.OrderItemDeleteView.as_view(), name="orderitem-delete"),
    
    # Payment URLs
    path("<int:order_pk>/payments/new/", views.PaymentCreateView.as_view(), name="payment-create"),
    path("payments/<int:pk>/edit/", views.PaymentUpdateView.as_view(), name="payment-update"),
    path("payments/<int:pk>/delete/", views.PaymentDeleteView.as_view(), name="payment-delete"),
    
    # Shipment URLs
    path("<int:order_pk>/shipments/new/", views.ShipmentCreateView.as_view(), name="shipment-create"),
    path("shipments/<int:pk>/edit/", views.ShipmentUpdateView.as_view(), name="shipment-update"),
    path("shipments/<int:pk>/delete/", views.ShipmentDeleteView.as_view(), name="shipment-delete"),
]