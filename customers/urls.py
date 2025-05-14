from django.urls import path
from . import views
from . import views_excel

app_name = "customers"

urlpatterns = [
    # Customer URLs
    path("", views.CustomerListView.as_view(), name="customer-list"),
    path("new/", views.CustomerCreateView.as_view(), name="customer-create"),
    path("<int:pk>/", views.CustomerDetailView.as_view(), name="customer-detail"),
    path("<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer-update"),
    path("<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer-delete"),
    
    # Address URLs
    path("<int:customer_pk>/addresses/new/", views.AddressCreateView.as_view(), name="address-create"),
    path("addresses/<int:pk>/edit/", views.AddressUpdateView.as_view(), name="address-update"),
    path("addresses/<int:pk>/delete/", views.AddressDeleteView.as_view(), name="address-delete"),
    
    # Contact URLs
    path("<int:customer_pk>/contacts/new/", views.ContactCreateView.as_view(), name="contact-create"),
    path("contacts/<int:pk>/edit/", views.ContactUpdateView.as_view(), name="contact-update"),
    path("contacts/<int:pk>/delete/", views.ContactDeleteView.as_view(), name="contact-delete"),
    
    # Excel Import/Export URLs
    path("export/", views_excel.export_customers, name="export_customers"),
    path("export/addresses/", views_excel.export_addresses, name="export_addresses"),
    path("import/", views_excel.CustomerImportView.as_view(), name="customer_import"),
    path("import/addresses/", views_excel.AddressImportView.as_view(), name="address_import"),
    path("template/", views_excel.generate_customer_template, name="generate_customer_template"),
    path("template/addresses/", views_excel.generate_address_template, name="generate_address_template"),
]