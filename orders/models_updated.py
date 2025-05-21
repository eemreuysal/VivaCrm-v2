"""
Orders modülü model tanımlamaları.
Clean Code prensipleriyle yeniden düzenlendi.
"""
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal, ROUND_DOWN
import logging

from customers.models import Customer, Address
from products.models import Product

try:
    from core.db_optimizations import OptimizedManager
except ImportError:
    # Fallback to default manager if optimization not available
    OptimizedManager = models.Manager

logger = logging.getLogger(__name__)


class OrderManager(OptimizedManager):
    """Order model için özelleştirilmiş manager."""
    
    def active(self):
        """Aktif (iptal edilmemiş) siparişleri döndür."""
        return self.exclude(status__in=['cancelled', 'refunded'])
    
    def pending_payment(self):
        """Ödeme bekleyen siparişleri döndür."""
        return self.filter(payment_status='pending')
    
    def pending_processing(self):
        """İşleme alınması gereken siparişleri döndür."""
        return self.filter(status='pending', payment_status='paid')
    
    def pending_shipment(self):
        """Kargolanması gereken siparişleri döndür."""
        return self.filter(status='processing')
    
    def recent(self, days=30):
        """Son belirli gün içindeki siparişleri döndür."""
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=days)
        return self.filter(order_date__gte=start_date)
    
    def with_items(self):
        """Sipariş kalemleri ile birlikte getir."""
        return self.prefetch_related('items', 'items__product')
    
    def with_customer(self):
        """Müşteri ile birlikte getir."""
        return self.select_related('customer')
    
    def with_addresses(self):
        """Adresler ile birlikte getir."""
        return self.select_related('billing_address', 'shipping_address')
    
    def with_all_relations(self):
        """Tüm ilişkiler ile birlikte getir."""
        return self.select_related(
            'customer', 
            'owner', 
            'billing_address', 
            'shipping_address'
        ).prefetch_related(
            'items', 
            'items__product',
            'payments',
            'shipments'
        )
    
    def by_segment(self, segment_code):
        """Belirli bir segmentteki siparişleri döndür."""
        return self.filter(segment=segment_code)
    
    def by_status(self, status):
        """Belirli bir durumdaki siparişleri döndür."""
        return self.filter(status=status)
    
    def by_payment_status(self, payment_status):
        """Belirli bir ödeme durumundaki siparişleri döndür."""
        return self.filter(payment_status=payment_status)
    
    def get_order_counts_by_status(self):
        """Durum bazında sipariş sayısını döndür."""
        return self.values('status').annotate(count=models.Count('id'))
    
    def get_order_totals_by_period(self, period_field='order_date__month'):
        """Belirli bir periyot bazında sipariş toplamlarını döndür."""
        return self.values(period_field).annotate(
            total=models.Sum('total_amount'),
            count=models.Count('id')
        )


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
    subtotal = models.DecimalField(_("Ara Toplam"), max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("KDV Tutarı"), max_digits=15, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(_("Kargo Ücreti"), max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_("İndirim Tutarı"), max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(_("Toplam Tutar"), max_digits=15, decimal_places=2, default=0)
    
    # Relations
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_orders",
        verbose_name=_("Sorumlu Kişi"),
        null=True, blank=True
    )
    
    # Fulfillment segment field
    segment = models.CharField(
        max_length=10,
        choices=[
            ('FBA', 'Fulfillment by Amazon'),
            ('FBM', 'Fulfillment by Merchant'),
        ],
        null=True,
        blank=True,
        verbose_name=_("Fulfillment Tipi")
    )
    
    # Managers
    objects = OrderManager()
    
    class Meta:
        verbose_name = _("Sipariş")
        verbose_name_plural = _("Siparişler")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['payment_status', 'status']),
            models.Index(fields=['order_date', 'status']),
            models.Index(fields=['total_amount', 'status']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['segment', 'status']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name if self.customer else ''}"
    
    def get_absolute_url(self):
        return reverse("orders:order-detail", kwargs={"pk": self.pk})
    
    def get_status_badge(self):
        """Sipariş durumu için CSS badge sınıfını döndür"""
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
        """Ödeme durumu için CSS badge sınıfını döndür"""
        status_classes = {
            'pending': 'badge-warning',
            'paid': 'badge-success',
            'partially_paid': 'badge-info',
            'refunded': 'badge-error',
            'cancelled': 'badge-error',
        }
        return status_classes.get(self.payment_status, 'badge-ghost')
    
    @property
    def is_editable(self):
        """Sipariş düzenlenebilir mi?"""
        return self.status in ['draft', 'pending', 'processing']
    
    @property
    def is_cancellable(self):
        """Sipariş iptal edilebilir mi?"""
        return self.status in ['draft', 'pending', 'processing']
    
    @property
    def can_be_shipped(self):
        """Sipariş kargoya verilebilir mi?"""
        return self.status == 'processing' and self.payment_status in ['paid', 'partially_paid']
    
    @property
    def is_paid(self):
        """Sipariş tamamen ödendi mi?"""
        return self.payment_status == 'paid'
    
    @property
    def total_paid_amount(self):
        """Toplam ödenen tutar"""
        paid = self.payments.filter(is_successful=True).aggregate(total=Sum('amount'))
        return paid['total'] or Decimal('0.00')
    
    @property
    def remaining_payment(self):
        """Kalan ödeme tutarı"""
        return max(Decimal('0.00'), self.total_amount - self.total_paid_amount)
    
    @property
    def items_count(self):
        """Toplam sipariş kalemi sayısı"""
        return self.items.count()
    
    @property
    def total_items_quantity(self):
        """Toplam ürün miktarı"""
        quantities = self.items.aggregate(total=Sum('quantity'))
        return quantities['total'] or 0
    
    @property
    def has_shipping_info(self):
        """Kargo bilgisi var mı?"""
        return self.shipments.exists()
        

class OrderItemManager(models.Manager):
    """OrderItem model için özelleştirilmiş manager."""
    
    def with_product(self):
        """Ürün ile birlikte getir."""
        return self.select_related('product')
    
    def with_order(self):
        """Sipariş ile birlikte getir."""
        return self.select_related('order')
    
    def with_all_relations(self):
        """Tüm ilişkiler ile birlikte getir."""
        return self.select_related('order', 'product')
    
    def by_product(self, product):
        """Belirli bir ürüne ait sipariş kalemlerini döndür."""
        if isinstance(product, Product):
            product_id = product.id
        else:
            product_id = product
        return self.filter(product_id=product_id)
    
    def most_ordered_products(self, limit=10):
        """En çok sipariş edilen ürünleri döndür."""
        return self.values('product').annotate(
            total_quantity=Sum('quantity'),
            order_count=models.Count('order', distinct=True)
        ).order_by('-total_quantity')[:limit]


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
    unit_price = models.DecimalField(_("Birim Fiyat"), max_digits=15, decimal_places=2)
    tax_rate = models.IntegerField(_("KDV Oranı (%)"), default=18)
    discount_amount = models.DecimalField(_("İndirim Tutarı"), max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(_("Notlar"), blank=True)
    
    # Manager
    objects = OrderItemManager()
    
    class Meta:
        verbose_name = _("Sipariş Kalemi")
        verbose_name_plural = _("Sipariş Kalemleri")
        ordering = ['id']
        indexes = [
            models.Index(fields=['order', 'product']),
            models.Index(fields=['product', 'quantity']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} ({self.quantity})"
    
    @property
    def line_total(self):
        """Vergi hariç satır toplamı"""
        result = (self.unit_price * self.quantity) - self.discount_amount
        return Decimal(str(result)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    @property
    def tax_amount(self):
        """KDV tutarı"""
        result = (self.line_total * self.tax_rate) / 100
        return Decimal(str(result)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    @property
    def total_with_tax(self):
        """Vergi dahil satır toplamı"""
        result = self.line_total + self.tax_amount
        return Decimal(str(result)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    @property
    def discount_percentage(self):
        """İndirim yüzdesi"""
        if self.discount_amount <= 0 or self.unit_price <= 0 or self.quantity <= 0:
            return 0
        
        total_before_discount = self.unit_price * self.quantity
        percentage = (self.discount_amount / total_before_discount) * 100
        return round(percentage, 2)


class PaymentManager(models.Manager):
    """Payment model için özelleştirilmiş manager."""
    
    def successful(self):
        """Başarılı ödemeleri döndür."""
        return self.filter(is_successful=True)
    
    def with_order(self):
        """Sipariş ile birlikte getir."""
        return self.select_related('order')
    
    def by_method(self, method):
        """Belirli bir ödeme yöntemine göre filtrele."""
        return self.filter(payment_method=method)
    
    def recent(self, days=30):
        """Son belirli gün içindeki ödemeleri döndür."""
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=days)
        return self.filter(payment_date__gte=start_date)
    
    def get_payment_totals_by_method(self):
        """Ödeme yöntemine göre toplam tutarları döndür."""
        return self.filter(is_successful=True).values('payment_method').annotate(
            total=Sum('amount'),
            count=models.Count('id')
        )


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
    
    # Manager
    objects = PaymentManager()
    
    class Meta:
        verbose_name = _("Ödeme")
        verbose_name_plural = _("Ödemeler")
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['order', 'payment_date']),
            models.Index(fields=['payment_method', 'is_successful']),
            models.Index(fields=['payment_date', 'is_successful']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_payment_method_display()} - {self.amount} ₺"


class ShipmentManager(models.Manager):
    """Shipment model için özelleştirilmiş manager."""
    
    def with_order(self):
        """Sipariş ile birlikte getir."""
        return self.select_related('order')
    
    def by_status(self, status):
        """Belirli bir duruma göre filtrele."""
        return self.filter(status=status)
    
    def by_carrier(self, carrier):
        """Belirli bir kargo firmasına göre filtrele."""
        return self.filter(carrier=carrier)
    
    def recent(self, days=30):
        """Son belirli gün içindeki kargoları döndür."""
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=days)
        return self.filter(shipping_date__gte=start_date)
    
    def delivered(self):
        """Teslim edilmiş kargoları döndür."""
        return self.filter(status='delivered')
    
    def in_transit(self):
        """Taşıma sırasındaki kargoları döndür."""
        return self.filter(status__in=['shipped', 'in_transit'])
    
    def get_shipment_counts_by_status(self):
        """Durum bazında kargo sayısını döndür."""
        return self.values('status').annotate(count=models.Count('id'))
    
    def get_shipment_counts_by_carrier(self):
        """Kargo firması bazında kargo sayısını döndür."""
        return self.values('carrier').annotate(count=models.Count('id'))


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
    
    # Manager
    objects = ShipmentManager()
    
    class Meta:
        verbose_name = _("Kargo")
        verbose_name_plural = _("Kargolar")
        ordering = ['-shipping_date']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['tracking_number']),
            models.Index(fields=['shipping_date', 'status']),
            models.Index(fields=['carrier', 'status']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.carrier} - {self.tracking_number}"
    
    def get_status_badge(self):
        """Kargo durumu için CSS badge sınıfını döndür"""
        status_classes = {
            'preparing': 'badge-warning',
            'shipped': 'badge-info',
            'in_transit': 'badge-info',
            'delivered': 'badge-success',
            'returned': 'badge-error',
            'failed': 'badge-error',
        }
        return status_classes.get(self.status, 'badge-ghost')
    
    @property
    def is_trackable(self):
        """Kargo takip edilebilir mi?"""
        return bool(self.tracking_number) and self.status in ['shipped', 'in_transit']
    
    @property
    def is_late(self):
        """Kargo gecikti mi?"""
        if not self.estimated_delivery or self.status in ['delivered', 'returned', 'failed']:
            return False
        return timezone.now() > self.estimated_delivery