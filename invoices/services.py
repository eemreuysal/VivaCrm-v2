from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
import os
import uuid
from datetime import timedelta

from .models import Invoice, InvoiceItem
from orders.models import Order


class InvoiceService:
    """
    Service class for invoice operations.
    """
    
    @staticmethod
    def generate_invoice_number():
        """
        Generate a unique invoice number.
        Format: INV-YYYYMM-XXXX where XXXX is a sequential number.
        """
        today = timezone.now()
        year = today.year
        month = today.month
        
        # Get count of invoices for this month
        count = Invoice.objects.filter(
            issue_date__year=year, 
            issue_date__month=month
        ).count() + 1
        
        return f"INV-{year}{month:02d}-{count:04d}"
    
    @staticmethod
    def create_invoice_from_order(order, created_by=None, invoice_type='standard', due_days=15):
        """
        Create a new invoice from an order.
        
        Args:
            order: The Order object
            created_by: User who creates the invoice
            invoice_type: Type of invoice ('standard', 'proforma', 'credit')
            due_days: Number of days until payment is due
        
        Returns:
            The created Invoice object
        """
        # Check if order already has an invoice of the same type
        existing_invoice = Invoice.objects.filter(
            order=order,
            invoice_type=invoice_type,
            status__in=['draft', 'issued', 'paid']
        ).first()
        
        if existing_invoice:
            return existing_invoice
        
        # Create new invoice
        invoice = Invoice.objects.create(
            invoice_number=InvoiceService.generate_invoice_number(),
            order=order,
            invoice_type=invoice_type,
            status='draft',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=due_days),
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            shipping_cost=order.shipping_cost,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            notes=_("Otomatik oluşturulmuş fatura"),
            created_by=created_by
        )
        
        # Create invoice items from order items
        for order_item in order.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"{order_item.product.name} (x{order_item.quantity})",
                quantity=order_item.quantity,
                unit_price=order_item.unit_price,
                tax_rate=order_item.tax_rate,
                discount_amount=order_item.discount_amount
            )
        
        return invoice
    
    @staticmethod
    def generate_pdf(invoice):
        """
        Generate PDF for an invoice using the InvoicePDFGenerator.
        
        Args:
            invoice: The Invoice object
        
        Returns:
            Generated PDF content (or HTML content if PDF generation fails)
        """
        from .pdf import InvoicePDFGenerator
        
        # Generate PDF using the generator class
        pdf_content, _ = InvoicePDFGenerator.generate_invoice_pdf(invoice, save_to_model=True)
        
        # If PDF generation failed, return HTML content
        if pdf_content is None:
            return invoice.html_content
            
        return pdf_content
    
    @staticmethod
    def send_invoice_email(invoice, request=None, custom_message=None):
        """
        Send an email to the customer with the invoice details.
        
        Args:
            invoice: The Invoice object
            request: The HTTP request object (used for building absolute URLs)
            custom_message: Optional custom message to include in the email
            
        Returns:
            Boolean indicating if the email was sent successfully
        """
        customer = invoice.order.customer
        if not customer.email:
            return False
            
        # Prepare context for email template
        context = {
            'invoice': invoice,
            'order': invoice.order,
            'customer': customer,
            'custom_message': custom_message,
            'company': {
                'name': 'VivaCRM Ltd.',
                'address': 'İstanbul, Türkiye',
                'phone': '+90 212 123 4567',
                'email': 'info@vivacrm.com',
                'website': 'www.vivacrm.com',
                'tax_id': '1234567890',
            }
        }
        
        # Build invoice URL
        if request:
            protocol = 'https' if request.is_secure() else 'http'
            domain = get_current_site(request).domain
            # Assuming there's a route named 'invoices:invoice-pdf'
            url_path = reverse('invoices:invoice-pdf', kwargs={'pk': invoice.pk})
            invoice_url = f"{protocol}://{domain}{url_path}"
            context['invoice_url'] = invoice_url
            context['company_logo_url'] = f"{protocol}://{domain}{settings.STATIC_URL}images/logo.png"
        
        # Render email templates
        html_content = render_to_string('emails/invoices/invoice_email.html', context)
        text_content = render_to_string('emails/invoices/invoice_email.txt', context)
        
        # Create email
        subject = f"Fatura: {invoice.invoice_number} - {customer.name}"
        from_email = settings.DEFAULT_FROM_EMAIL or 'info@vivacrm.com'
        to_email = customer.email
        
        # Create and send email
        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            
            # Attach PDF if available
            if invoice.pdf_file and hasattr(invoice.pdf_file, 'path') and os.path.exists(invoice.pdf_file.path):
                msg.attach_file(invoice.pdf_file.path)
            else:
                # Generate PDF on-the-fly if not already available
                from .pdf import InvoicePDFGenerator
                pdf_content, filename = InvoicePDFGenerator.generate_invoice_pdf(invoice, save_to_model=False)
                if pdf_content:
                    msg.attach(filename, pdf_content, 'application/pdf')
                
            msg.send()
            
            # Update invoice sent status
            invoice.is_sent = True
            invoice.sent_date = timezone.now()
            invoice.save(update_fields=['is_sent', 'sent_date'])
            
            return True
        except Exception as e:
            # Log the error (in a production environment)
            print(f"Error sending invoice email: {e}")
            return False