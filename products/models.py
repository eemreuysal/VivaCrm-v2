from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
try:
    from core.db_optimizations import OptimizedManager
except ImportError:
    # Fallback to default manager if optimization not available
    OptimizedManager = models.Manager


class Category(models.Model):
    """
    Product category model.
    Used to categorize products.
    """
    name = models.CharField(_("Kategori Adı"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True)
    description = models.TextField(_("Açıklama"), blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name=_("Üst Kategori"),
        null=True, blank=True
    )
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Kategori")
        verbose_name_plural = _("Kategoriler")
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'slug']),
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['parent', 'is_active']),
        ]
        
    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name
        
    def get_absolute_url(self):
        return reverse("products:category-detail", kwargs={"slug": self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductFamily(models.Model):
    """
    Product family model.
    Used to group related products.
    """
    name = models.CharField(_("Aile Adı"), max_length=255)  # Karakter sınırını 100'den 255'e yükselttik
    slug = models.SlugField(_("Slug"), max_length=255, unique=True)  # Slug sınırını da yükselttik
    description = models.TextField(_("Açıklama"), blank=True)
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Ürün Ailesi")
        verbose_name_plural = _("Ürün Aileleri")
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['slug', 'is_active']),
        ]
        
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product model for VivaCRM.
    Stores information about products.
    """
    STATUS_CHOICES = (
        ('available', _('Satışta')),
        ('unavailable', _('Satışta Değil')),
        ('coming_soon', _('Yakında')),
        ('discontinued', _('Üretimden Kalktı')),
    )
    
    TAX_RATE_CHOICES = (
        (0, '0%'),
        (1, '1%'),
        (8, '8%'),
        (10, '10%'),
        (18, '18%'),
        (20, '20%'),
    )
    
    code = models.CharField(_("Ürün Kodu"), max_length=50, unique=True)
    name = models.CharField(_("Ürün Adı"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, unique=True)
    description = models.TextField(_("Açıklama"), blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name=_("Kategori"),
        null=True, blank=True
    )
    family = models.ForeignKey(
        ProductFamily, 
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name=_("Ürün Ailesi"),
        null=True, blank=True
    )
    
    # Pricing
    price = models.DecimalField(_("Fiyat"), max_digits=10, decimal_places=2)
    cost = models.DecimalField(_("Maliyet"), max_digits=10, decimal_places=2, null=True, blank=True)
    tax_rate = models.IntegerField(_("KDV Oranı (%)"), choices=TAX_RATE_CHOICES, default=18)
    discount_price = models.DecimalField(_("İndirimli Fiyat"), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventory
    stock = models.PositiveIntegerField(_("Stok Miktarı"), default=0)
    threshold_stock = models.PositiveIntegerField(_("Kritik Stok Seviyesi"), default=5, 
        help_text=_("Stok bu seviyenin altına düştüğünde uyarı verilir"))
    is_physical = models.BooleanField(_("Fiziksel Ürün"), default=True)
    weight = models.DecimalField(_("Ağırlık (kg)"), max_digits=6, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(_("Boyutlar (U x G x Y)"), max_length=50, blank=True)
    sku = models.CharField(_("SKU"), max_length=50, blank=True)
    barcode = models.CharField(_("Barkod"), max_length=50, blank=True)
    asin = models.CharField(_("ASIN"), max_length=50, blank=True, help_text=_("Amazon Standard Identification Number"))
    
    # Status
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='available')
    is_featured = models.BooleanField(_("Öne Çıkan"), default=False)
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    # Managers
    objects = OptimizedManager()
    
    # Default query optimization hints
    default_select_related = ['category', 'family']
    default_prefetch_related = ['images', 'stock_movements']
    
    class Meta:
        verbose_name = _("Ürün")
        verbose_name_plural = _("Ürünler")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['stock', 'threshold_stock']),
            models.Index(fields=['price', 'is_active']),
            models.Index(fields=['created_at', 'is_active']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['barcode']),
            models.Index(fields=['sku']),
        ]
        
    def __str__(self):
        return f"{self.code} - {self.name}"
        
    def get_absolute_url(self):
        return reverse("products:product-detail", kwargs={"slug": self.slug})
    
    @property
    def tax_amount(self):
        from decimal import Decimal
        if self.tax_rate is not None:
            rate = Decimal(str(self.tax_rate)) / Decimal('100')
            if self.discount_price and self.discount_price > 0:
                return round(self.discount_price * rate, 2)
            return round(self.price * rate, 2)
        return Decimal('0')
    
    @property
    def price_with_tax(self):
        from decimal import Decimal
        tax = self.tax_amount
        if self.discount_price and self.discount_price > 0:
            return round(self.discount_price + tax, 2)
        return round(self.price + tax, 2)
    
    @property
    def profit_margin(self):
        from decimal import Decimal
        if self.cost and self.cost > 0:
            hundred = Decimal('100')
            if self.discount_price and self.discount_price > 0:
                return round(((self.discount_price - self.cost) / self.cost) * hundred, 2)
            return round(((self.price - self.cost) / self.cost) * hundred, 2)
        return None
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """
    Product image model.
    Each product can have multiple images.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Ürün")
    )
    image = models.ImageField(_("Görsel"), upload_to="products/")
    alt_text = models.CharField(_("Alt Metin"), max_length=255, blank=True)
    is_primary = models.BooleanField(_("Ana Görsel"), default=False)
    order = models.PositiveIntegerField(_("Sıra"), default=0)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Ürün Görseli")
        verbose_name_plural = _("Ürün Görselleri")
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['product', 'order']),
        ]
        
    def __str__(self):
        return f"{self.product.name} - {self.order}"


class ProductAttribute(models.Model):
    """
    Product attribute model.
    Used for product specifications like color, size, material etc.
    """
    name = models.CharField(_("Özellik Adı"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True)
    description = models.TextField(_("Açıklama"), blank=True)
    is_active = models.BooleanField(_("Aktif"), default=True)
    
    class Meta:
        verbose_name = _("Ürün Özelliği")
        verbose_name_plural = _("Ürün Özellikleri")
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['slug', 'is_active']),
        ]
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductAttributeValue(models.Model):
    """
    Product attribute value model.
    Stores the values of attributes for products.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name="attribute_values",
        verbose_name=_("Ürün")
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name=_("Özellik")
    )
    value = models.CharField(_("Değer"), max_length=255)
    
    class Meta:
        verbose_name = _("Ürün Özellik Değeri")
        verbose_name_plural = _("Ürün Özellik Değerleri")
        unique_together = ('product', 'attribute')
        indexes = [
            models.Index(fields=['product', 'attribute']),
            models.Index(fields=['attribute', 'value']),
        ]
        
    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"


class StockMovement(models.Model):
    """
    Model to track stock movements (additions and deductions).
    """
    MOVEMENT_TYPE_CHOICES = (
        ('purchase', _('Satın Alma')),
        ('sale', _('Satış')),
        ('return', _('İade')),
        ('adjustment', _('Stok Düzeltme')),
        ('inventory', _('Envanter Sayımı')),
        ('transfer', _('Transfer')),
        ('waste', _('Fire')),
    )
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name="stock_movements",
        verbose_name=_("Ürün")
    )
    movement_type = models.CharField(
        _("Hareket Tipi"), 
        max_length=20, 
        choices=MOVEMENT_TYPE_CHOICES
    )
    quantity = models.IntegerField(_("Miktar"))
    reference = models.CharField(_("Referans"), max_length=255, blank=True)
    notes = models.TextField(_("Notlar"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name=_("Oluşturan")
    )
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    previous_stock = models.PositiveIntegerField(_("Önceki Stok"), default=0)
    new_stock = models.PositiveIntegerField(_("Yeni Stok"), default=0)
    unit_cost = models.DecimalField(_("Birim Maliyet"), max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = _("Stok Hareketi")
        verbose_name_plural = _("Stok Hareketleri")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['movement_type', 'created_at']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['reference']),
        ]
        
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        try:
            # Store previous stock level
            if self.pk is None:  # Only on creation
                self.previous_stock = self.product.stock
                
                # Update product stock based on movement type
                if self.movement_type in ['purchase', 'return', 'adjustment', 'inventory']:
                    self.new_stock = self.previous_stock + self.quantity
                else:  # sale, waste, transfer
                    self.new_stock = max(0, self.previous_stock - abs(self.quantity))
                
                # Update product cost if provided
                if self.unit_cost and self.movement_type == 'purchase':
                    # Calculate weighted average cost if there's existing stock
                    if self.previous_stock > 0 and self.product.cost:
                        total_old_value = self.previous_stock * self.product.cost
                        total_new_value = self.quantity * self.unit_cost
                        self.product.cost = (total_old_value + total_new_value) / self.new_stock
                    else:
                        self.product.cost = self.unit_cost
        except Exception as e:
            # Log and handle any calculation errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in StockMovement.save(): {str(e)}")
            # Set safe default values
            if not hasattr(self, 'previous_stock'):
                self.previous_stock = 0
            if not hasattr(self, 'new_stock'):
                self.new_stock = 0
                    
        super().save(*args, **kwargs)


@receiver(post_save, sender=StockMovement)
def update_product_stock(sender, instance, created, **kwargs):
    """
    Update product stock level when a stock movement is created.
    """
    if created:
        product = instance.product
        product.stock = instance.new_stock
        # Only update cost if unit_cost is provided
        update_fields = ['stock']
        if instance.unit_cost:
            update_fields.append('cost')
        product.save(update_fields=update_fields)