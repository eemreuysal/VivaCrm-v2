from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum

from customers.models import Customer, Address
from products.models import Product


class Order(models.Model):
    """
    Order model for VivaCRM.
    Stores information about customer orders.
    """
    STATUS_CHOICES = (
        ('draft', _('Taslak')),
        ('pending', _('Beklemede')),
        ('processing', _('İşleniyor')),
        ('shipped', _('Kargoya Verildi')),
        ('delivered', _('Teslim Edildi')),
        ('completed', _('Tamamlandı')),
        ('cancelled', _('İptal Edildi')),
        ('refunded', _('İade Edildi')),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Beklemede')),
        ('paid', _('Ödendi')),
        ('partially_paid', _('Kısmen Ödendi')),
        ('refunded', _('İade Edildi')),
        ('cancelled', _('İptal Edildi')),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', _('Kredi Kartı')),
        ('bank_transfer', _('Banka Havalesi')),
        ('cash', _('Nakit')),
        ('online_payment', _('Online Ödeme')),
        ('other', _('Diğer')),
    )
    
    # Order information
    order_number = models.CharField(_("Sipariş Numarası"), max_length=50, unique=True)
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Müşteri")
    )
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(_("Notlar"), blank=True)
    
    # Dates
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    order_date = models.DateTimeField(_("Sipariş Tarihi"), default=timezone.now)
    shipping_date = models.DateTimeField(_("Kargo Tarihi"), null=True, blank=True)
    delivery_date = models.DateTimeField(_("Teslim Tarihi"), null=True, blank=True)
    
    # Address information
    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        related_name="billing_orders",
        verbose_name=_("Fatura Adresi"),
        null=True, blank=True
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        related_name="shipping_orders",
        verbose_name=_("Teslimat Adresi"),
        null=True, blank=True
    )
    
    # Payment information
    payment_method = models.CharField(_("Ödeme Yöntemi"), max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_status = models.CharField(_("Ödeme Durumu"), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_notes = models.TextField(_("Ödeme Notları"), blank=True)
    
    # Amounts
    subtotal = models.DecimalField(_("Ara Toplam"), max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("KDV Tutarı"), max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(_("Kargo Ücreti"), max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_("İndirim Tutarı"), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_("Toplam Tutar"), max_digits=10, decimal_places=2, default=0)
    
    # Relations
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_orders",
        verbose_name=_("Sorumlu Kişi"),
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = _("Sipariş")
        verbose_name_plural = _("Siparişler")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"
    
    def get_absolute_url(self):
        return reverse("orders:order-detail", kwargs={"pk": self.pk})
    
    def calculate_totals(self):
        """Calculate all price fields based on order items"""
        # Calculate subtotal
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        
        # Calculate tax
        self.tax_amount = sum(item.tax_amount for item in items)
        
        # Calculate total
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        
        self.save()
    
    def get_status_badge(self):
        """Return appropriate CSS class for the order status badge"""
        status_classes = {
            'draft': 'badge-ghost',
            'pending': 'badge-warning',
            'processing': 'badge-info',
            'shipped': 'badge-info',
            'delivered': 'badge-success',
            'completed': 'badge-success',
            'cancelled': 'badge-error',
            'refunded': 'badge-error',
        }
        return status_classes.get(self.status, 'badge-ghost')
    
    def get_payment_status_badge(self):
        """Return appropriate CSS class for the payment status badge"""
        status_classes = {
            'pending': 'badge-warning',
            'paid': 'badge-success',
            'partially_paid': 'badge-info',
            'refunded': 'badge-error',
            'cancelled': 'badge-error',
        }
        return status_classes.get(self.payment_status, 'badge-ghost')


class OrderItem(models.Model):
    """
    Order item model.
    Represents a product in an order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Sipariş")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name=_("Ürün")
    )
    quantity = models.PositiveIntegerField(_("Miktar"), default=1)
    unit_price = models.DecimalField(_("Birim Fiyat"), max_digits=10, decimal_places=2)
    tax_rate = models.IntegerField(_("KDV Oranı (%)"), default=18)
    discount_amount = models.DecimalField(_("İndirim Tutarı"), max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(_("Notlar"), blank=True)
    
    class Meta:
        verbose_name = _("Sipariş Kalemi")
        verbose_name_plural = _("Sipariş Kalemleri")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} ({self.quantity})"
    
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


class Payment(models.Model):
    """
    Payment model.
    Tracks payments made for orders.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("Sipariş")
    )
    payment_method = models.CharField(_("Ödeme Yöntemi"), max_length=20, choices=Order.PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(_("Tutar"), max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(_("Ödeme Tarihi"), default=timezone.now)
    transaction_id = models.CharField(_("İşlem Numarası"), max_length=100, blank=True)
    notes = models.TextField(_("Notlar"), blank=True)
    is_successful = models.BooleanField(_("Başarılı"), default=True)
    
    class Meta:
        verbose_name = _("Ödeme")
        verbose_name_plural = _("Ödemeler")
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_payment_method_display()} - {self.amount} ₺"


class Shipment(models.Model):
    """
    Shipment model.
    Tracks shipments for orders.
    """
    STATUS_CHOICES = (
        ('preparing', _('Hazırlanıyor')),
        ('shipped', _('Kargoya Verildi')),
        ('in_transit', _('Taşınıyor')),
        ('delivered', _('Teslim Edildi')),
        ('returned', _('İade Edildi')),
        ('failed', _('Başarısız')),
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="shipments",
        verbose_name=_("Sipariş")
    )
    carrier = models.CharField(_("Kargo Firması"), max_length=100)
    tracking_number = models.CharField(_("Takip Numarası"), max_length=100, blank=True)
    shipping_date = models.DateTimeField(_("Kargoya Verilme Tarihi"), default=timezone.now)
    estimated_delivery = models.DateTimeField(_("Tahmini Teslimat"), null=True, blank=True)
    actual_delivery = models.DateTimeField(_("Gerçekleşen Teslimat"), null=True, blank=True)
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='preparing')
    notes = models.TextField(_("Notlar"), blank=True)
    
    class Meta:
        verbose_name = _("Kargo")
        verbose_name_plural = _("Kargolar")
        ordering = ['-shipping_date']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.carrier} - {self.tracking_number}"
    
    def get_status_badge(self):
        """Return appropriate CSS class for the shipment status badge"""
        status_classes = {
            'preparing': 'badge-warning',
            'shipped': 'badge-info',
            'in_transit': 'badge-info',
            'delivered': 'badge-success',
            'returned': 'badge-error',
            'failed': 'badge-error',
        }
        return status_classes.get(self.status, 'badge-ghost')