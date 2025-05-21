"""
Customers modülü model tanımlamaları.
Clean Code prensipleriyle yeniden düzenlendi.
"""
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Sum
import logging

try:
    from core.db_optimizations import OptimizedManager
except ImportError:
    # Optimization not available
    OptimizedManager = models.Manager

logger = logging.getLogger(__name__)


class CustomerManager(OptimizedManager):
    """Customer model için özelleştirilmiş manager."""
    
    def active(self):
        """Aktif müşterileri döndür."""
        return self.filter(is_active=True)
    
    def inactive(self):
        """Pasif müşterileri döndür."""
        return self.filter(is_active=False)
    
    def individuals(self):
        """Bireysel müşterileri döndür."""
        return self.filter(type='individual')
    
    def corporate(self):
        """Kurumsal müşterileri döndür."""
        return self.filter(type='corporate')
    
    def with_orders(self):
        """Siparişi olan müşterileri döndür."""
        return self.filter(orders__isnull=False).distinct()
    
    def with_addresses(self):
        """Adres bilgisi olan müşterileri döndür."""
        return self.prefetch_related('addresses')
    
    def with_contacts(self):
        """İletişim kişileri olan müşterileri döndür."""
        return self.prefetch_related('contacts')
    
    def with_all_relations(self):
        """Tüm ilişkili verilerle birlikte müşterileri döndür."""
        return self.select_related('owner').prefetch_related(
            'addresses', 'contacts', 'orders'
        )
    
    def search(self, query):
        """Ad, email veya telefona göre müşteri ara."""
        return self.filter(
            models.Q(name__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(phone__icontains=query) |
            models.Q(company_name__icontains=query)
        )
    
    def get_top_customers(self, limit=10):
        """En çok alışveriş yapan müşterileri döndür."""
        return self.annotate(
            total_purchases=Sum('orders__total_amount')
        ).order_by('-total_purchases')[:limit]


class Customer(models.Model):
    """
    Customer model for VivaCRM.
    Stores information about customers.
    """
    CUSTOMER_TYPE_CHOICES = (
        ('individual', _('Bireysel')),
        ('corporate', _('Kurumsal')),
    )
    
    name = models.CharField(_("Adı"), max_length=255)
    type = models.CharField(_("Müşteri Tipi"), max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='individual')
    company_name = models.CharField(_("Şirket Adı"), max_length=255, blank=True)
    tax_office = models.CharField(_("Vergi Dairesi"), max_length=255, blank=True)
    tax_number = models.CharField(_("Vergi No / TC Kimlik No"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Telefon"), max_length=20, blank=True)
    website = models.URLField(_("Web Sitesi"), blank=True)
    notes = models.TextField(_("Notlar"), blank=True)
    
    # Customer status
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_at = models.DateTimeField(_("Kayıt Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Son Güncelleme"), auto_now=True)
    
    # Ownership and relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_customers",
        verbose_name=_("Sorumlu Kişi"),
        null=True, blank=True
    )
    
    # Manager
    objects = CustomerManager()
    
    class Meta:
        verbose_name = _("Müşteri")
        verbose_name_plural = _("Müşteriler")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['created_at', 'is_active']),
        ]
        
    def __str__(self):
        if self.type == 'corporate' and self.company_name:
            return self.company_name
        return self.name
        
    def get_absolute_url(self):
        return reverse("customers:customer-detail", kwargs={"pk": self.pk})
        
    @property
    def total_orders(self):
        """Toplam sipariş sayısı"""
        return self.orders.count()
        
    @property
    def total_revenue(self):
        """Toplam gelir"""
        from django.db.models import Sum
        total = self.orders.filter(status='completed').aggregate(Sum('total_amount'))
        return total['total_amount__sum'] or 0
    
    @property
    def display_name(self):
        """Görüntülenecek isim"""
        if self.type == 'corporate' and self.company_name:
            return f"{self.company_name} ({self.name})"
        return self.name
    
    @property
    def primary_address(self):
        """Varsayılan adres"""
        return self.addresses.filter(is_default=True).first()
    
    @property
    def primary_contact(self):
        """Birincil ilgili kişi"""
        return self.contacts.filter(is_primary=True).first()
    
    @property
    def billing_address(self):
        """Fatura adresi"""
        # Önce varsayılan fatura adresi
        address = self.addresses.filter(type='billing', is_default=True).first()
        if not address:
            # Herhangi bir fatura adresi
            address = self.addresses.filter(type='billing').first()
        if not address:
            # Varsayılan herhangi bir adres
            address = self.addresses.filter(is_default=True).first()
        if not address:
            # Herhangi bir adres
            address = self.addresses.first()
        return address
    
    @property
    def shipping_address(self):
        """Teslimat adresi"""
        # Önce varsayılan teslimat adresi
        address = self.addresses.filter(type='shipping', is_default=True).first()
        if not address:
            # Herhangi bir teslimat adresi
            address = self.addresses.filter(type='shipping').first()
        if not address:
            # Varsayılan herhangi bir adres
            address = self.addresses.filter(is_default=True).first()
        if not address:
            # Herhangi bir adres
            address = self.addresses.first()
        return address
    
    @property
    def last_order_date(self):
        """Son sipariş tarihi"""
        last_order = self.orders.order_by('-order_date').first()
        return last_order.order_date if last_order else None
    
    @property
    def has_complete_info(self):
        """Müşteri bilgileri tam mı?"""
        # Temel bilgilerin varlığını kontrol et
        has_contact = bool(self.email or self.phone)
        has_address = self.addresses.exists()
        
        if self.type == 'corporate':
            # Kurumsal müşteri için ek kontroller
            has_tax_info = bool(self.tax_number and self.tax_office)
            return has_contact and has_address and has_tax_info
        else:
            # Bireysel müşteri için
            return has_contact and has_address


class AddressManager(models.Manager):
    """Address model için özelleştirilmiş manager."""
    
    def default_addresses(self):
        """Varsayılan adresleri döndür."""
        return self.filter(is_default=True)
    
    def billing_addresses(self):
        """Fatura adreslerini döndür."""
        return self.filter(type='billing')
    
    def shipping_addresses(self):
        """Teslimat adreslerini döndür."""
        return self.filter(type='shipping')
    
    def with_customer(self):
        """Müşteri ile birlikte adresleri döndür."""
        return self.select_related('customer')


class Address(models.Model):
    """
    Customer address model.
    Each customer can have multiple addresses.
    """
    ADDRESS_TYPE_CHOICES = (
        ('billing', _('Fatura Adresi')),
        ('shipping', _('Teslimat Adresi')),
        ('other', _('Diğer')),
    )
    
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("Müşteri")
    )
    title = models.CharField(_("Adres Başlığı"), max_length=100)
    type = models.CharField(_("Adres Tipi"), max_length=20, choices=ADDRESS_TYPE_CHOICES, default='other')
    address_line1 = models.CharField(_("Adres Satırı 1"), max_length=255)
    address_line2 = models.CharField(_("Adres Satırı 2"), max_length=255, blank=True)
    city = models.CharField(_("Şehir"), max_length=100)
    state = models.CharField(_("İlçe"), max_length=100, blank=True)
    postal_code = models.CharField(_("Posta Kodu"), max_length=20, blank=True)
    country = models.CharField(_("Ülke"), max_length=100, default='Türkiye')
    is_default = models.BooleanField(_("Varsayılan"), default=False)
    
    # Manager
    objects = AddressManager()
    
    class Meta:
        verbose_name = _("Adres")
        verbose_name_plural = _("Adresler")
        ordering = ['-is_default', 'title']
        indexes = [
            models.Index(fields=['customer', 'is_default']),
            models.Index(fields=['customer', 'type']),
            models.Index(fields=['city', 'customer']),
        ]
        
    def __str__(self):
        return f"{self.title} - {self.customer}"
    
    @property
    def full_address(self):
        """Tam adres formatı"""
        address_parts = [self.address_line1]
        
        if self.address_line2:
            address_parts.append(self.address_line2)
            
        location_parts = []
        if self.state:
            location_parts.append(self.state)
        if self.city:
            location_parts.append(self.city)
        if location_parts:
            address_parts.append(", ".join(location_parts))
            
        if self.postal_code:
            address_parts.append(self.postal_code)
            
        if self.country:
            address_parts.append(self.country)
            
        return "\n".join(address_parts)
    
    @property
    def one_line_address(self):
        """Tek satır adres formatı"""
        address_parts = [self.address_line1]
        
        if self.address_line2:
            address_parts.append(self.address_line2)
            
        location_parts = []
        if self.state:
            location_parts.append(self.state)
        if self.city:
            location_parts.append(self.city)
        if location_parts:
            address_parts.append(", ".join(location_parts))
            
        if self.postal_code:
            address_parts.append(self.postal_code)
            
        if self.country:
            address_parts.append(self.country)
            
        return ", ".join(address_parts)


class ContactManager(models.Manager):
    """Contact model için özelleştirilmiş manager."""
    
    def primary_contacts(self):
        """Birincil kişileri döndür."""
        return self.filter(is_primary=True)
    
    def with_customer(self):
        """Müşteri ile birlikte kişileri döndür."""
        return self.select_related('customer')


class Contact(models.Model):
    """
    Contact person model for corporate customers.
    Each corporate customer can have multiple contact persons.
    """
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name=_("Müşteri")
    )
    name = models.CharField(_("Ad Soyad"), max_length=255)
    title = models.CharField(_("Unvan"), max_length=100, blank=True)
    department = models.CharField(_("Departman"), max_length=100, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Telefon"), max_length=20, blank=True)
    is_primary = models.BooleanField(_("Birincil Kişi"), default=False)
    notes = models.TextField(_("Notlar"), blank=True)
    
    # Manager
    objects = ContactManager()
    
    class Meta:
        verbose_name = _("İlgili Kişi")
        verbose_name_plural = _("İlgili Kişiler")
        ordering = ['-is_primary', 'name']
        indexes = [
            models.Index(fields=['customer', 'is_primary']),
            models.Index(fields=['name']),
            models.Index(fields=['email']),
        ]
        
    def __str__(self):
        return f"{self.name} - {self.customer}"
    
    @property
    def full_title(self):
        """Tam unvan ve departman"""
        parts = []
        if self.title:
            parts.append(self.title)
        if self.department:
            parts.append(self.department)
        if parts:
            return ", ".join(parts)
        return ""
    
    @property
    def has_contact_info(self):
        """İletişim bilgisi var mı?"""
        return bool(self.email or self.phone)