"""
Product attribute views for products app.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from products.models import Product, ProductAttribute, ProductAttributeValue
from products.forms.attribute import ProductAttributeForm, ProductAttributeValueForm


class ProductAttributeListView(LoginRequiredMixin, ListView):
    model = ProductAttribute
    template_name = 'products/attribute_list.html'
    context_object_name = 'attributes'


class ProductAttributeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProductAttribute
    form_class = ProductAttributeForm
    template_name = 'products/attribute_form.html'
    success_url = reverse_lazy('products:attribute-list')
    success_message = _("Ürün özelliği başarıyla oluşturuldu.")


class ProductAttributeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProductAttribute
    form_class = ProductAttributeForm
    template_name = 'products/attribute_form.html'
    success_url = reverse_lazy('products:attribute-list')
    success_message = _("Ürün özelliği başarıyla güncellendi.")


class ProductAttributeDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ProductAttribute
    template_name = 'products/attribute_confirm_delete.html'
    success_url = reverse_lazy('products:attribute-list')
    success_message = _("Ürün özelliği başarıyla silindi.")


class ProductAttributeValueCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProductAttributeValue
    form_class = ProductAttributeValueForm
    template_name = 'products/attribute_value_form.html'
    success_message = _("Ürün özellik değeri başarıyla eklendi.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        kwargs['product'] = product
        return kwargs
    
    def form_valid(self, form):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        form.instance.product = product
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.kwargs['slug']})


class ProductAttributeValueUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProductAttributeValue
    fields = ['value']
    template_name = 'products/attribute_value_form.html'
    success_message = _("Ürün özellik değeri başarıyla güncellendi.")
    
    def get_success_url(self):
        return reverse('products:product-detail', kwargs={'slug': self.object.product.slug})


class ProductAttributeValueDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductAttributeValue
    
    def delete(self, request, *args, **kwargs):
        value = self.get_object()
        product_slug = value.product.slug
        value.delete()
        return JsonResponse({
            'success': True,
            'message': _("Ürün özellik değeri başarıyla silindi.")
        })
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)