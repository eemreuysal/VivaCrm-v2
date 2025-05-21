from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.

class TestComponentsView(TemplateView):
    """Alpine.js bileşenlerini ve tema entegrasyonunu test etmek için görünüm.
    Bu sayfa, projedeki tüm bileşenleri ve özellikleri test etmek için kullanılır.
    """
    template_name = "test_components.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Bileşen Testi"
        return context