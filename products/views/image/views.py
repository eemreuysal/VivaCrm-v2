"""
Product image views for products app.
"""
from django.views.generic import CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from products.models import Product, ProductImage
from products.forms.image import ProductImageForm


class ProductImageCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProductImage
    form_class = ProductImageForm
    template_name = 'products/product_image_form.html'
    success_message = _("Ürün görseli başarıyla eklendi.")
    
    def form_valid(self, form):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        form.instance.product = product
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.kwargs['slug']})


class ProductImageDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductImage
    
    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        product_slug = image.product.slug
        image.delete()
        return JsonResponse({
            'success': True,
            'message': _("Ürün görseli başarıyla silindi.")
        })
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)