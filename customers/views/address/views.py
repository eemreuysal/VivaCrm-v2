"""
Adres view'ları - müşterilere ait adreslerin yönetimi
"""
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from customers.models import Customer, Address
from customers.forms import AddressForm


class AddressCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = 'customers/address_form.html'
    success_message = _("Adres başarıyla eklendi.")
    
    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs['customer_pk'])
        form.instance.customer = customer
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('customers:customer-detail', kwargs={'pk': self.kwargs['customer_pk']})


class AddressUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Address
    form_class = AddressForm
    template_name = 'customers/address_form.html'
    success_message = _("Adres başarıyla güncellendi.")
    
    def get_success_url(self):
        return reverse('customers:customer-detail', kwargs={'pk': self.object.customer.pk})


class AddressDeleteView(LoginRequiredMixin, DeleteView):
    model = Address
    
    def delete(self, request, *args, **kwargs):
        address = self.get_object()
        customer_pk = address.customer.pk
        address.delete()
        return JsonResponse({
            'success': True,
            'message': _("Adres başarıyla silindi.")
        })
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)