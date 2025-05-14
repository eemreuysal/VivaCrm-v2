from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Customer, Address, Contact
from .forms import CustomerForm, AddressForm, ContactForm, CustomerSearchForm


class CustomerListView(LoginRequiredMixin, FormMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 10
    form_class = CustomerSearchForm
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form = self.get_form()
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            customer_type = form.cleaned_data.get('customer_type')
            is_active = form.cleaned_data.get('is_active')
            
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) | 
                    Q(company_name__icontains=query) | 
                    Q(email__icontains=query) | 
                    Q(phone__icontains=query)
                )
            
            if customer_type:
                queryset = queryset.filter(type=customer_type)
                
            if is_active:
                queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_initial(self):
        return {
            'query': self.request.GET.get('query', ''),
            'customer_type': self.request.GET.get('customer_type', ''),
            'is_active': self.request.GET.get('is_active', True),
        }


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add forms for adding new address and contact
        context['address_form'] = AddressForm()
        context['contact_form'] = ContactForm()
        return context


class CustomerCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_message = _("Müşteri başarıyla oluşturuldu.")
    
    def get_success_url(self):
        return reverse('customers:customer-detail', kwargs={'pk': self.object.pk})


class CustomerUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_message = _("Müşteri bilgileri başarıyla güncellendi.")
    
    def get_success_url(self):
        return reverse('customers:customer-detail', kwargs={'pk': self.object.pk})


class CustomerDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customers:customer-list')
    success_message = _("Müşteri başarıyla silindi.")


# Address Views
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


# Contact Views
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