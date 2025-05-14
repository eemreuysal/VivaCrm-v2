from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import os

from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemForm, InvoiceSearchForm
from .services import InvoiceService
from orders.models import Order


class InvoiceListView(LoginRequiredMixin, FormMixin, ListView):
    """
    View for listing invoices with search and filters.
    """
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    form_class = InvoiceSearchForm
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form = self.get_form()
        
        if form.is_valid():
            # Apply search filters
            query = form.cleaned_data.get('query')
            status = form.cleaned_data.get('status')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            show_paid = form.cleaned_data.get('show_paid')
            show_unpaid = form.cleaned_data.get('show_unpaid')
            
            # Text search
            if query:
                queryset = queryset.filter(
                    Q(invoice_number__icontains=query) | 
                    Q(order__order_number__icontains=query) |
                    Q(order__customer__name__icontains=query) |
                    Q(order__customer__company_name__icontains=query)
                )
            
            # Status filter
            if status:
                queryset = queryset.filter(status=status)
                
            # Date range filter
            if start_date:
                queryset = queryset.filter(issue_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(issue_date__lte=end_date)
                
            # Payment status filter
            payment_filters = []
            if show_paid:
                payment_filters.append('paid')
            if show_unpaid:
                payment_filters.extend(['draft', 'issued'])
                
            if payment_filters and len(payment_filters) < 3:  # If not all selected
                queryset = queryset.filter(status__in=payment_filters)
        
        return queryset
    
    def get_initial(self):
        return {
            'query': self.request.GET.get('query', ''),
            'status': self.request.GET.get('status', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'show_paid': self.request.GET.get('show_paid', True),
            'show_unpaid': self.request.GET.get('show_unpaid', True),
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary data
        context['total_amount'] = Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        context['unpaid_amount'] = Invoice.objects.exclude(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
        context['paid_amount'] = Invoice.objects.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Add counts
        context['draft_count'] = Invoice.objects.filter(status='draft').count()
        context['issued_count'] = Invoice.objects.filter(status='issued').count()
        context['paid_count'] = Invoice.objects.filter(status='paid').count()
        
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying invoice details.
    """
    model = Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['order'] = self.object.order
        context['customer'] = self.object.order.customer
        return context


class InvoiceCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    View for creating a new invoice.
    """
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_message = _("Fatura başarıyla oluşturuldu.")
    
    def get_initial(self):
        initial = super().get_initial()
        initial['invoice_number'] = InvoiceService.generate_invoice_number()
        return initial
    
    def dispatch(self, request, *args, **kwargs):
        # Get order if provided in URL
        self.order = None
        order_id = self.kwargs.get('order_id')
        if order_id:
            self.order = get_object_or_404(Order, pk=order_id)
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.order:
            kwargs['order'] = self.order
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.order:
            context['order'] = self.order
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class InvoiceUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    View for updating an invoice.
    """
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'
    context_object_name = 'invoice'
    success_message = _("Fatura başarıyla güncellendi.")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice_items'] = self.object.items.all()
        context['is_edit'] = True
        return context


class InvoiceDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    View for deleting an invoice.
    """
    model = Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoices:invoice-list')
    success_message = _("Fatura başarıyla silindi.")


class InvoiceItemCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    View for adding an item to an invoice.
    """
    model = InvoiceItem
    form_class = InvoiceItemForm
    template_name = 'invoices/invoice_item_form.html'
    success_message = _("Fatura kalemi başarıyla eklenmiştir.")
    
    def dispatch(self, request, *args, **kwargs):
        self.invoice = get_object_or_404(Invoice, pk=self.kwargs['invoice_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = self.invoice
        return context
    
    def form_valid(self, form):
        form.instance.invoice = self.invoice
        response = super().form_valid(form)
        
        # Update invoice totals
        self.invoice.subtotal = sum(item.line_total for item in self.invoice.items.all())
        self.invoice.tax_amount = sum(item.tax_amount for item in self.invoice.items.all())
        self.invoice.total_amount = self.invoice.subtotal + self.invoice.tax_amount + self.invoice.shipping_cost - self.invoice.discount_amount
        self.invoice.save()
        
        return response
    
    def get_success_url(self):
        return reverse('invoices:invoice-detail', kwargs={'pk': self.invoice.pk})


class InvoiceItemUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    View for updating an invoice item.
    """
    model = InvoiceItem
    form_class = InvoiceItemForm
    template_name = 'invoices/invoice_item_form.html'
    context_object_name = 'item'
    success_message = _("Fatura kalemi başarıyla güncellenmiştir.")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = self.object.invoice
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Update invoice totals
        invoice = self.object.invoice
        invoice.subtotal = sum(item.line_total for item in invoice.items.all())
        invoice.tax_amount = sum(item.tax_amount for item in invoice.items.all())
        invoice.total_amount = invoice.subtotal + invoice.tax_amount + invoice.shipping_cost - invoice.discount_amount
        invoice.save()
        
        return response
    
    def get_success_url(self):
        return reverse('invoices:invoice-detail', kwargs={'pk': self.object.invoice.pk})


class InvoiceItemDeleteView(LoginRequiredMixin, View):
    """
    View for deleting an invoice item.
    """
    def post(self, request, *args, **kwargs):
        item = get_object_or_404(InvoiceItem, pk=kwargs['pk'])
        invoice = item.invoice
        
        item.delete()
        
        # Update invoice totals
        invoice.subtotal = sum(item.line_total for item in invoice.items.all())
        invoice.tax_amount = sum(item.tax_amount for item in invoice.items.all())
        invoice.total_amount = invoice.subtotal + invoice.tax_amount + invoice.shipping_cost - invoice.discount_amount
        invoice.save()
        
        messages.success(request, _("Fatura kalemi başarıyla silinmiştir."))
        return redirect('invoices:invoice-detail', pk=invoice.pk)


class GenerateInvoicePDFView(LoginRequiredMixin, View):
    """
    View for generating and viewing invoice PDF.
    """
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=kwargs['pk'])
        
        try:
            # Check if we already have a PDF file
            if invoice.pdf_file and hasattr(invoice.pdf_file, 'path') and os.path.exists(invoice.pdf_file.path):
                # Use existing PDF file
                return FileResponse(open(invoice.pdf_file.path, 'rb'), 
                                   content_type='application/pdf')
            
            # Generate PDF
            from .pdf import InvoicePDFGenerator
            pdf_content, filename = InvoicePDFGenerator.generate_invoice_pdf(invoice)
            
            # Update invoice status if it's still draft
            if invoice.status == 'draft':
                invoice.status = 'issued'
                invoice.save(update_fields=['status'])
            
            # If PDF generation failed, return HTML content
            if pdf_content is None:
                # Return HTML content
                return HttpResponse(invoice.html_content, content_type='text/html')
            
            # Return PDF file
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
            
        except Exception as e:
            messages.error(request, _(f"Fatura görüntüleme hatası: {str(e)}"))
            return redirect('invoices:invoice-detail', pk=invoice.pk)


class DownloadInvoicePDFView(LoginRequiredMixin, View):
    """
    View for downloading invoice PDF.
    """
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=kwargs['pk'])
        
        try:
            # Check if we already have a PDF file
            if invoice.pdf_file and hasattr(invoice.pdf_file, 'path') and os.path.exists(invoice.pdf_file.path):
                # Use existing PDF file
                return FileResponse(
                    open(invoice.pdf_file.path, 'rb'),
                    content_type='application/pdf',
                    as_attachment=True,
                    filename=f"invoice_{invoice.invoice_number}.pdf"
                )
            
            # Generate PDF
            from .pdf import InvoicePDFGenerator
            pdf_content, filename = InvoicePDFGenerator.generate_invoice_pdf(invoice)
            
            # If PDF generation failed, return error
            if pdf_content is None:
                messages.error(request, _("PDF oluşturulamadı. WeasyPrint kütüphanesi eksik olabilir."))
                return redirect('invoices:invoice-detail', pk=invoice.pk)
            
            # Return PDF file as attachment
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            messages.error(request, _(f"Fatura indirme hatası: {str(e)}"))
            return redirect('invoices:invoice-detail', pk=invoice.pk)


class CreateInvoiceFromOrderView(LoginRequiredMixin, View):
    """
    View for creating an invoice from an order.
    """
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['order_id'])
        
        try:
            # Create invoice from order
            invoice = InvoiceService.create_invoice_from_order(
                order=order,
                created_by=request.user
            )
            
            messages.success(request, _("Fatura başarıyla oluşturuldu."))
            return redirect('invoices:invoice-detail', pk=invoice.pk)
        except Exception as e:
            messages.error(request, _(f"Fatura oluşturma hatası: {str(e)}"))
            return redirect('orders:order-detail', pk=order.pk)


class SendInvoiceEmailView(LoginRequiredMixin, View):
    """
    View for sending an invoice via email.
    """
    def post(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=kwargs['pk'])
        
        # Check if the invoice is in a state that can be sent
        if invoice.status == 'draft':
            messages.warning(request, _("Taslak faturalar gönderilemez. Lütfen önce durumu 'Kesildi' olarak değiştirin."))
            return redirect('invoices:invoice-detail', pk=invoice.pk)
        
        # If customer email is missing
        if not invoice.order.customer.email:
            messages.error(request, _("Müşterinin e-posta adresi bulunmamaktadır. Fatura gönderilemedi."))
            return redirect('invoices:invoice-detail', pk=invoice.pk)
            
        # Get custom message from form (if provided)
        custom_message = request.POST.get('custom_message', '')
        
        # Try to send the email
        success = InvoiceService.send_invoice_email(
            invoice=invoice,
            request=request,
            custom_message=custom_message
        )
        
        if success:
            messages.success(request, _("Fatura e-posta ile başarıyla gönderildi."))
        else:
            messages.error(request, _("Fatura gönderilirken bir hata oluştu. Lütfen tekrar deneyin."))
            
        return redirect('invoices:invoice-detail', pk=invoice.pk)