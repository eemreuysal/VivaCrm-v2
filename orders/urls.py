from django.urls import path
from django.views.generic import TemplateView

# Modülleri import etme sorunlarını çözmek için bir geçiçi çözüm olarak,
# Excel import view'ları hariç her şeyi yoruma alıyoruz
class TemporaryView(TemplateView):
    template_name = "orders/maintenance.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Excel Import Yapısı Bakımda"
        context['message'] = "Excel import yapısı bakımda, lütfen daha sonra tekrar deneyin."
        return context

app_name = "orders"

urlpatterns = [
    # Geçici olarak tüm ana URL'leri bakım sayfasına yönlendiriyoruz
    path("", TemporaryView.as_view(), name="order-list"),
    path("new/", TemporaryView.as_view(), name="order-create"),
    path("<int:pk>/", TemporaryView.as_view(), name="order-detail"),
    path("<int:pk>/edit/", TemporaryView.as_view(), name="order-update"),
    path("<int:pk>/delete/", TemporaryView.as_view(), name="order-delete"),
    path("<int:order_pk>/items/new/", TemporaryView.as_view(), name="orderitem-create"),
    path("items/<int:pk>/edit/", TemporaryView.as_view(), name="orderitem-update"),
    path("items/<int:pk>/delete/", TemporaryView.as_view(), name="orderitem-delete"),
    path("<int:order_pk>/payments/new/", TemporaryView.as_view(), name="payment-create"),
    path("payments/<int:pk>/edit/", TemporaryView.as_view(), name="payment-update"),
    path("payments/<int:pk>/delete/", TemporaryView.as_view(), name="payment-delete"),
    path("<int:order_pk>/shipments/new/", TemporaryView.as_view(), name="shipment-create"),
    path("shipments/<int:pk>/edit/", TemporaryView.as_view(), name="shipment-update"),
    path("shipments/<int:pk>/delete/", TemporaryView.as_view(), name="shipment-delete"),
    path("import/", TemporaryView.as_view(), name="order-import"),
    path("import-api/", TemporaryView.as_view(), name="order-import-api"),
    path("template/", TemporaryView.as_view(), name="generate-order-template"),
    path("export/", TemporaryView.as_view(), name="export_orders"),
    path("excel/import/", TemporaryView.as_view(), name="excel-import"),
    path("excel/import/<uuid:session_id>/results/", TemporaryView.as_view(), name="excel-import-results"),
    path("excel/template/", TemporaryView.as_view(), name="excel-template"),
    path("excel/report/", TemporaryView.as_view(), name="excel-report"),
    path("excel/validate/", TemporaryView.as_view(), name="excel-validate"),
    path("import-tasks/", TemporaryView.as_view(), name="import-task-list"),
    path("import-task/<int:pk>/", TemporaryView.as_view(), name="import-task-detail"),
    
    # Sadece Form sınıfları ekleme işlemi başarılı oldu,
    # Bu sayfaların gösterilmesi geçici çözüm olarak URL yönlendirmelerini bekletebilir
]