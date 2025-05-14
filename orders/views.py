from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone

from customers.models import Customer, Address
from products.models import Product
from .models import Order, OrderItem, Payment, Shipment
from .forms import OrderForm, OrderItemForm, PaymentForm, ShipmentForm, OrderSearchForm


class OrderListView(LoginRequiredMixin, FormMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    form_class = OrderSearchForm
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form = self.get_form()
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            status = form.cleaned_data.get('status')
            payment_status = form.cleaned_data.get('payment_status')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            if query:
                queryset = queryset.filter(
                    Q(order_number__icontains=query) | 
                    Q(customer__name__icontains=query) | 
                    Q(customer__company_name__icontains=query)
                )
            
            if status:
                queryset = queryset.filter(status=status)
                
            if payment_status:
                queryset = queryset.filter(payment_status=payment_status)
                
            if date_from:
                queryset = queryset.filter(order_date__gte=date_from)
                
            if date_to:
                # Add one day to include the end date
                queryset = queryset.filter(order_date__lte=date_to)
        
        return queryset
    
    def get_initial(self):
        return {
            'query': self.request.GET.get('query', ''),
            'status': self.request.GET.get('status', ''),
            'payment_status': self.request.GET.get('payment_status', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_item_form'] = OrderItemForm(order=self.object)
        context['payment_form'] = PaymentForm(order=self.object)
        context['shipment_form'] = ShipmentForm()
        return context


class OrderCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_message = _("Sipariş başarıyla oluşturuldu.")
    
    def form_valid(self, form):
        # Set the owner to the current user if not specified
        if not form.cleaned_data.get('owner'):
            form.instance.owner = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        messages.success(self.request, self.success_message)
        return reverse('orders:order-detail', kwargs={'pk': self.object.pk})


class OrderUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_message = _("Sipariş başarıyla güncellendi.")
    
    def get_success_url(self):
        return reverse('orders:order-detail', kwargs={'pk': self.object.pk})


class OrderDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Order
    template_name = 'orders/order_confirm_delete.html'
    success_url = reverse_lazy('orders:order-list')
    success_message = _("Sipariş başarıyla silindi.")


class AjaxableResponseMixin:
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.is_ajax():
            data = {
                'success': True,
                'message': self.success_message,
            }
            return JsonResponse(data)
        else:
            return response


# OrderItem Views
class OrderItemCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = OrderItem
    form_class = OrderItemForm
    template_name = 'orders/orderitem_form.html'
    success_message = _("Ürün başarıyla eklendi.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.order = get_object_or_404(Order, pk=self.kwargs['order_pk'])
        kwargs['order'] = self.order
        return kwargs
    
    def form_valid(self, form):
        form.instance.order = self.order
        
        # Use product price and tax if not specified
        if form.instance.product and not form.instance.unit_price:
            if form.instance.product.discount_price and form.instance.product.discount_price > 0:
                form.instance.unit_price = form.instance.product.discount_price
            else:
                form.instance.unit_price = form.instance.product.price
            
        if form.instance.product and not form.instance.tax_rate:
            form.instance.tax_rate = form.instance.product.tax_rate
            
        return super().form_valid(form)
    
    def get_success_url(self):
        messages.success(self.request, self.success_message)
        return reverse('orders:order-detail', kwargs={'pk': self.order.pk})


class OrderItemUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = OrderItem
    form_class = OrderItemForm
    template_name = 'orders/orderitem_form.html'
    success_message = _("Ürün başarıyla güncellendi.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.object.order
        return kwargs
    
    def get_success_url(self):
        return reverse('orders:order-detail', kwargs={'pk': self.object.order.pk})


class OrderItemDeleteView(LoginRequiredMixin, DeleteView):
    model = OrderItem
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        order_pk = self.object.order.pk
        self.object.delete()
        
        if request.is_ajax():
            return JsonResponse({
                'success': True,
                'message': _("Ürün başarıyla silindi.")
            })
        else:
            messages.success(request, _("Ürün başarıyla silindi."))
            return HttpResponseRedirect(reverse('orders:order-detail', kwargs={'pk': order_pk}))
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# Payment Views
class PaymentCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'orders/payment_form.html'
    success_message = _("Ödeme başarıyla eklendi.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.order = get_object_or_404(Order, pk=self.kwargs['order_pk'])
        kwargs['order'] = self.order
        return kwargs
    
    def form_valid(self, form):
        form.instance.order = self.order
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orders:order-detail', kwargs={'pk': self.order.pk})


class PaymentUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'orders/payment_form.html'
    success_message = _("Ödeme başarıyla güncellendi.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.object.order
        return kwargs
    
    def get_success_url(self):
        return reverse('orders:order-detail', kwargs={'pk': self.object.order.pk})


class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = Payment
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        order_pk = self.object.order.pk
        self.object.delete()
        
        if request.is_ajax():
            return JsonResponse({
                'success': True,
                'message': _("Ödeme başarıyla silindi.")
            })
        else:
            messages.success(request, _("Ödeme başarıyla silindi."))
            return HttpResponseRedirect(reverse('orders:order-detail', kwargs={'pk': order_pk}))
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


# Shipment Views
class ShipmentCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Shipment
    form_class = ShipmentForm
    template_name = 'orders/shipment_form.html'
    success_message = _("Kargo bilgisi başarıyla eklendi.")
    
    def form_valid(self, form):
        order = get_object_or_404(Order, pk=self.kwargs['order_pk'])
        form.instance.order = order
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orders:order-detail', kwargs={'pk': self.kwargs['order_pk']})


class ShipmentUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Shipment
    form_class = ShipmentForm
    template_name = 'orders/shipment_form.html'
    success_message = _("Kargo bilgisi başarıyla güncellendi.")
    
    def get_success_url(self):
        return reverse('orders:order-detail', kwargs={'pk': self.object.order.pk})


class ShipmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Shipment
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        order_pk = self.object.order.pk
        self.object.delete()
        
        if request.is_ajax():
            return JsonResponse({
                'success': True,
                'message': _("Kargo bilgisi başarıyla silindi.")
            })
        else:
            messages.success(request, _("Kargo bilgisi başarıyla silindi."))
            return HttpResponseRedirect(reverse('orders:order-detail', kwargs={'pk': order_pk}))
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)