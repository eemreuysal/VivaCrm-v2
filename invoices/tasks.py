from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import os
import uuid
from .models import Invoice
from .services import InvoiceService


@shared_task
def send_invoice_email(invoice_id):
    """
    Send an invoice to the customer by email, including the PDF attachment.
    """
    try:
        invoice = Invoice.objects.select_related('customer', 'order').get(id=invoice_id)
    except Invoice.DoesNotExist:
        return f"Invoice with ID {invoice_id} not found"
    
    # Generate PDF
    pdf_content = InvoiceService.generate_pdf(invoice)
    pdf_path = f"/tmp/invoice_{invoice.invoice_number}_{uuid.uuid4().hex}.pdf"
    
    # Save PDF to temporary file
    with open(pdf_path, 'wb') as f:
        f.write(pdf_content)
    
    # Prepare email context
    context = {
        'invoice': invoice,
        'customer': invoice.customer,
        'company_name': 'VivaCRM',
    }
    
    # Render email templates
    text_content = render_to_string('emails/invoices/invoice_email.txt', context)
    html_content = render_to_string('emails/invoices/invoice_email.html', context)
    
    # Create email message
    subject = f'Invoice #{invoice.invoice_number} from VivaCRM'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = invoice.customer.email
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    
    # Attach PDF if it exists
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
            filename = f"Invoice_{invoice.invoice_number}.pdf"
            msg.attach(filename, pdf_data, 'application/pdf')
    
    # Send email
    msg.send()
    
    # Update invoice status
    invoice.is_sent = True
    invoice.sent_date = timezone.now()
    invoice.save(update_fields=['is_sent', 'sent_date'])
    
    return f"Invoice #{invoice.invoice_number} sent to {to_email}"


@shared_task
def send_payment_reminder(days=7):
    """
    Send payment reminders for unpaid invoices that are past due.
    """
    # Get unpaid invoices that are past due by the specified number of days
    cutoff_date = timezone.now().date() - timedelta(days=days)
    overdue_invoices = Invoice.objects.filter(
        is_paid=False,
        due_date__lt=cutoff_date
    ).select_related('customer')
    
    count = 0
    for invoice in overdue_invoices:
        context = {
            'invoice': invoice,
            'customer': invoice.customer,
            'days_overdue': (timezone.now().date() - invoice.due_date).days,
            'total_amount': invoice.total_amount,
        }
        
        subject = f"Payment Reminder: Invoice #{invoice.invoice_number} is overdue"
        text_content = render_to_string('emails/invoices/payment_reminder.txt', context)
        html_content = render_to_string('emails/invoices/payment_reminder.html', context)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.customer.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        # Update the invoice to record that a reminder was sent
        invoice.last_reminder_date = timezone.now()
        invoice.reminder_count = invoice.reminder_count + 1 if invoice.reminder_count else 1
        invoice.save(update_fields=['last_reminder_date', 'reminder_count'])
        
        count += 1
    
    return f"Sent payment reminders for {count} overdue invoices"


@shared_task
def bulk_generate_invoices_for_completed_orders():
    """
    Automatically generate invoices for completed orders that don't have invoices yet.
    """
    from orders.models import Order
    
    # Find completed orders without invoices
    orders_needing_invoices = Order.objects.filter(
        status='completed',
        invoice__isnull=True
    ).select_related('customer')
    
    count = 0
    for order in orders_needing_invoices:
        # Create new invoice
        invoice = Invoice.objects.create(
            customer=order.customer,
            order=order,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            total_amount=order.total_amount,
            notes=f"Automatically generated for order #{order.order_number}"
        )
        
        # Create invoice items from order items
        for order_item in order.items.all():
            invoice.items.create(
                product=order_item.product,
                description=order_item.product.name,
                quantity=order_item.quantity,
                unit_price=order_item.price,
                total_price=order_item.price * order_item.quantity
            )
        
        count += 1
    
    return f"Generated {count} invoices for completed orders"