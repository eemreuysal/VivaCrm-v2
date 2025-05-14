from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings


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
    
    class Meta:
        verbose_name = _("Müşteri")
        verbose_name_plural = _("Müşteriler")
        ordering = ['-created_at']
        
    def __str__(self):
        if self.type == 'corporate' and self.company_name:
            return self.company_name
        return self.name
        
    def get_absolute_url(self):
        return reverse("customers:customer-detail", kwargs={"pk": self.pk})
        
    @property
    def total_orders(self):
        return self.orders.count()
        
    @property
    def total_revenue(self):
        from django.db.models import Sum
        total = self.orders.filter(status='completed').aggregate(Sum('total_amount'))
        return total['total_amount__sum'] or 0


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
    
    class Meta:
        verbose_name = _("Adres")
        verbose_name_plural = _("Adresler")
        ordering = ['-is_default', 'title']
        
    def __str__(self):
        return f"{self.title} - {self.customer}"


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
    
    class Meta:
        verbose_name = _("İlgili Kişi")
        verbose_name_plural = _("İlgili Kişiler")
        ordering = ['-is_primary', 'name']
        
    def __str__(self):
        return f"{self.name} - {self.customer}"