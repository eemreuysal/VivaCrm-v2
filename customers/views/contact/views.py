"""
İlgili kişi view'ları - müşterilere ait kişilerin yönetimi
"""
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from customers.models import Customer, Contact
from customers.forms import ContactForm


class ContactCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'customers/contact_form.html'
    success_message = _("İlgili kişi başarıyla eklendi.")
    
    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs['customer_pk'])
        form.instance.customer = customer
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('customers:customer-detail', kwargs={'pk': self.kwargs['customer_pk']})


class ContactUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'customers/contact_form.html'
    success_message = _("İlgili kişi başarıyla güncellendi.")
    
    def get_success_url(self):
        return reverse('customers:customer-detail', kwargs={'pk': self.object.customer.pk})


class ContactDeleteView(LoginRequiredMixin, DeleteView):
    model = Contact
    
    def delete(self, request, *args, **kwargs):
        contact = self.get_object()
        customer_pk = contact.customer.pk
        contact.delete()
        return JsonResponse({
            'success': True,
            'message': _("İlgili kişi başarıyla silindi.")
        })
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)