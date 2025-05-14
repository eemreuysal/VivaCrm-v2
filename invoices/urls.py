from django.urls import path
from . import views

app_name = "invoices"

urlpatterns = [
    # Invoice URLs
    path("", views.InvoiceListView.as_view(), name="invoice-list"),
    path("new/", views.InvoiceCreateView.as_view(), name="invoice-create"),
    path("new/order/<int:order_id>/", views.InvoiceCreateView.as_view(), name="invoice-create-from-order-form"),
    path("order/<int:order_id>/generate/", views.CreateInvoiceFromOrderView.as_view(), name="generate-from-order"),
    path("<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"),
    path("<int:pk>/edit/", views.InvoiceUpdateView.as_view(), name="invoice-update"),
    path("<int:pk>/delete/", views.InvoiceDeleteView.as_view(), name="invoice-delete"),
    path("<int:pk>/pdf/", views.GenerateInvoicePDFView.as_view(), name="invoice-pdf"),
    path("<int:pk>/pdf/download/", views.DownloadInvoicePDFView.as_view(), name="invoice-pdf-download"),
    path("<int:pk>/send-email/", views.SendInvoiceEmailView.as_view(), name="send-invoice-email"),
    
    # Invoice Item URLs
    path("<int:invoice_id>/items/new/", views.InvoiceItemCreateView.as_view(), name="invoice-item-create"),
    path("items/<int:pk>/edit/", views.InvoiceItemUpdateView.as_view(), name="invoice-item-update"),
    path("items/<int:pk>/delete/", views.InvoiceItemDeleteView.as_view(), name="invoice-item-delete"),
]