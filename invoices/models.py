from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import uuid
import os

from orders.models import Order


def invoice_pdf_path(instance, filename):
    """
    Generate a unique path for the invoice PDF
    Format: invoices/year/month/invoice_number.pdf
    """
    ext = filename.split('.')[-1]
    date = instance.issue_date
    path = f"invoices/{date.year}/{date.month:02d}"
    filename = f"{instance.invoice_number}.{ext}"
    return os.path.join(path, filename)


class Invoice(models.Model):
    """
    Invoice model for VivaCRM.
    Stores information about invoices generated for orders.
    """
    INVOICE_TYPE_CHOICES = (
        ('standard', _('Standart')),
        ('proforma', _('Proforma')),
        ('credit', _('İade')),
    )
    
    STATUS_CHOICES = (
        ('draft', _('Taslak')),
        ('issued', _('Kesildi')),
        ('paid', _('Ödendi')),
        ('cancelled', _('İptal Edildi')),
        ('refunded', _('İade Edildi')),
    )
    
    # Invoice information
    invoice_number = models.CharField(_("Fatura Numarası"), max_length=50, unique=True)
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name=_("Sipariş")
    )
    invoice_type = models.CharField(_("Fatura Tipi"), max_length=20, choices=INVOICE_TYPE_CHOICES, default='standard')
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    issue_date = models.DateField(_("Fatura Tarihi"), default=timezone.now)
    due_date = models.DateField(_("Son Ödeme Tarihi"), null=True, blank=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    # Amounts
    subtotal = models.DecimalField(_("Ara Toplam"), max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("KDV Tutarı"), max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(_("Kargo Ücreti"), max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_("İndirim Tutarı"), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_("Toplam Tutar"), max_digits=10, decimal_places=2, default=0)
    
    # PDF
    pdf_file = models.FileField(_("PDF Dosyası"), upload_to=invoice_pdf_path, null=True, blank=True)
    html_content = models.TextField(_("HTML İçeriği"), blank=True)
    
    # Additional information
    notes = models.TextField(_("Notlar"), blank=True)
    is_sent = models.BooleanField(_("Gönderildi"), default=False)
    sent_date = models.DateTimeField(_("Gönderilme Tarihi"), null=True, blank=True)
    
    # Relations
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_invoices",
        verbose_name=_("Oluşturan"),
        null=True
    )
    
    class Meta:
        verbose_name = _("Fatura")
        verbose_name_plural = _("Faturalar")
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.order.order_number}"
    
    def get_absolute_url(self):
        return reverse("invoices:invoice-detail", kwargs={"pk": self.pk})
    
    def get_status_badge(self):
        """Return appropriate CSS class for the invoice status badge"""
        status_classes = {
            'draft': 'badge-ghost',
            'issued': 'badge-info',
            'paid': 'badge-success',
            'cancelled': 'badge-error',
            'refunded': 'badge-error',
        }
        return status_classes.get(self.status, 'badge-ghost')
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['paid', 'cancelled', 'refunded']:
            return self.due_date < timezone.now().date()
        return False


class InvoiceItem(models.Model):
    """
    Invoice item model.
    Represents a line item in an invoice.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Fatura")
    )
    description = models.CharField(_("Açıklama"), max_length=255)
    quantity = models.PositiveIntegerField(_("Miktar"), default=1)
    unit_price = models.DecimalField(_("Birim Fiyat"), max_digits=10, decimal_places=2)
    tax_rate = models.IntegerField(_("KDV Oranı (%)"), default=18)
    discount_amount = models.DecimalField(_("İndirim Tutarı"), max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = _("Fatura Kalemi")
        verbose_name_plural = _("Fatura Kalemleri")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description} ({self.quantity})"
    
    @property
    def line_total(self):
        """Calculate total price for this item without tax"""
        return (self.unit_price * self.quantity) - self.discount_amount
    
    @property
    def tax_amount(self):
        """Calculate tax amount for this item"""
        return (self.line_total * self.tax_rate) / 100
    
    @property
    def total_with_tax(self):
        """Calculate total price with tax for this item"""
        return self.line_total + self.tax_amount