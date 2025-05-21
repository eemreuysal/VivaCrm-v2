"""
Core model mixins and abstract models for VivaCRM v2.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging
import uuid

logger = logging.getLogger(__name__)


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(
        _("created at"), auto_now_add=True, editable=False,
        help_text=_("Date and time when this record was created")
    )
    updated_at = models.DateTimeField(
        _("updated at"), auto_now=True, editable=False,
        help_text=_("Date and time when this record was last updated")
    )
    
    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    An abstract base class model that uses UUID as primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class ValidatedModel(models.Model):
    """
    An abstract base class model that provides enhanced validation.
    """
    
    class Meta:
        abstract = True
    
    def clean(self):
        """
        Perform model validation before saving.
        This method is called by full_clean() which should be called before saving.
        """
        super().clean()
        
        # Import here to avoid circular imports
        from core.validation import validate_model_integrity
        
        # Run the model-specific validation
        validate_model_integrity(self)
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure full_clean is called before saving.
        """
        # Only validate if not raw (used during migrations)
        if not kwargs.get('raw', False):
            self.full_clean()
        super().save(*args, **kwargs)


class SoftDeleteModel(models.Model):
    """
    An abstract base class model that implements soft deletion.
    """
    is_deleted = models.BooleanField(_("deleted"), default=False, db_index=True)
    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """
        Override delete method to implement soft deletion.
        """
        # Update flags in memory
        self.is_deleted = True
        self.deleted_at = timezone.now()
        
        # Save the object
        self.save(update_fields=['is_deleted', 'deleted_at'])
        
        # Log the deletion
        logger.info(f"{self.__class__.__name__} {self.pk} soft-deleted")
    
    def hard_delete(self, using=None, keep_parents=False):
        """
        Perform an actual deletion of the object.
        """
        # Log the hard deletion
        logger.warning(f"{self.__class__.__name__} {self.pk} hard-deleted")
        
        # Call the parent's delete method
        super().delete(using=using, keep_parents=keep_parents)


class SoftDeleteManager(models.Manager):
    """
    A manager that excludes soft-deleted objects by default.
    """
    def get_queryset(self):
        """
        Return a queryset excluding soft-deleted objects.
        """
        return super().get_queryset().filter(is_deleted=False)


class OwnedModel(models.Model):
    """
    An abstract base class model for objects owned by a user.
    """
    owner = models.ForeignKey(
        'accounts.User', 
        on_delete=models.CASCADE, 
        related_name="%(class)ss",
        verbose_name=_("owner"),
        help_text=_("User who owns this object")
    )
    
    class Meta:
        abstract = True


class AuditLogMixin(models.Model):
    """
    A mixin that provides fields for tracking when and by whom 
    objects were created and modified.
    """
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created",
        verbose_name=_("created by"),
        help_text=_("User who created this record")
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated",
        verbose_name=_("updated by"),
        help_text=_("User who last updated this record")
    )
    
    class Meta:
        abstract = True


class ValidationRule(models.Model):
    """Validation rule model."""
    
    RULE_TYPES = [
        ('required', _('Zorunlu Alan')),
        ('regex', _('Regex (Düzenli İfade)')),
        ('range', _('Sayı Aralığı')),
        ('length', _('Metin Uzunluğu')),
        ('choices', _('Seçenekler')),
        ('email', _('E-posta')),
        ('phone', _('Telefon')),
        ('url', _('URL')),
        ('tckn', _('TC Kimlik No')),
        ('date', _('Tarih')),
        ('custom', _('Özel')),
    ]
    
    name = models.CharField(_('Kural Adı'), max_length=100)
    rule_type = models.CharField(_('Kural Tipi'), max_length=20, choices=RULE_TYPES)
    parameters = models.JSONField(_('Parametreler'), default=dict)
    error_message = models.CharField(_('Hata Mesajı'), max_length=255, blank=True)
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Tarihi'), auto_now=True)
    
    class Meta:
        verbose_name = _('Doğrulama Kuralı')
        verbose_name_plural = _('Doğrulama Kuralları')
        db_table = 'validation_rules'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
    
    def to_dict(self):
        """Convert to dictionary format for rule creation."""
        data = {
            'type': self.rule_type,
            'message': self.error_message
        }
        data.update(self.parameters)
        return data


class RuleSet(models.Model):
    """Rule set for grouping validation rules."""
    
    name = models.CharField(_('Kural Seti Adı'), max_length=100)
    description = models.TextField(_('Açıklama'), blank=True)
    model_name = models.CharField(_('Model Adı'), max_length=100)
    field_name = models.CharField(_('Alan Adı'), max_length=100)
    rules = models.ManyToManyField(ValidationRule, verbose_name=_('Kurallar'))
    is_active = models.BooleanField(_('Aktif'), default=True)
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Tarihi'), auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rule_sets',
        verbose_name=_('Oluşturan')
    )
    
    class Meta:
        verbose_name = _('Kural Seti')
        verbose_name_plural = _('Kural Setleri')
        db_table = 'rule_sets'
        ordering = ['name']
        unique_together = [['model_name', 'field_name']]
    
    def __str__(self):
        return f"{self.name} ({self.model_name}.{self.field_name})"
    
    def get_rules(self):
        """Get rules as list of dictionaries."""
        return [rule.to_dict() for rule in self.rules.all()]
    
    def validate(self, value):
        """Validate value against all rules in the set."""
        from .validation_rules import RuleRegistry
        from django.core.exceptions import ValidationError
        
        errors = []
        for rule_data in self.get_rules():
            rule = RuleRegistry.create_from_dict(rule_data)
            if rule:
                try:
                    rule(value)
                except ValidationError as e:
                    errors.append(str(e.message))
        
        return errors


class ValidationLog(models.Model):
    """Log for validation activities."""
    
    rule_set = models.ForeignKey(
        RuleSet,
        on_delete=models.CASCADE,
        related_name='validation_logs',
        verbose_name=_('Kural Seti')
    )
    value = models.TextField(_('Değer'))
    is_valid = models.BooleanField(_('Geçerli'))
    errors = models.JSONField(_('Hatalar'), default=list)
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Doğrulama Logu')
        verbose_name_plural = _('Doğrulama Logları')
        db_table = 'validation_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rule_set.name} - {'Geçerli' if self.is_valid else 'Geçersiz'}"


class CustomFieldDefinition(TimeStampedModel):
    """Definition of custom fields for models"""
    
    SUPPORTED_MODELS = [
        ('product', _('Ürün')),
        ('order', _('Sipariş')),
        ('customer', _('Müşteri')),
        ('invoice', _('Fatura')),
    ]
    
    @property
    def FIELD_TYPE_CHOICES(self):
        from core.custom_fields import CustomFieldRegistry
        return CustomFieldRegistry.get_choices()
    
    model_name = models.CharField(
        _('Model Adı'),
        max_length=50,
        choices=SUPPORTED_MODELS,
        help_text=_('Özel alanın ekleneceği model')
    )
    field_name = models.CharField(
        _('Alan Adı'),
        max_length=50,
        help_text=_('Veritabanındaki alan adı (küçük harfler ve alt çizgi kullanın)')
    )
    label = models.CharField(
        _('Etiket'),
        max_length=100,
        help_text=_('Kullanıcıya gösterilecek alan adı')
    )
    field_type = models.CharField(
        _('Alan Tipi'),
        max_length=50,
        help_text=_('Alanın veri tipi')
    )
    help_text = models.CharField(
        _('Yardım Metni'),
        max_length=200,
        blank=True,
        help_text=_('Alan için açıklayıcı metin')
    )
    required = models.BooleanField(
        _('Zorunlu'),
        default=False,
        help_text=_('Bu alan zorunlu mu?')
    )
    default_value = models.TextField(
        _('Varsayılan Değer'),
        blank=True,
        help_text=_('Alan için varsayılan değer')
    )
    options = models.JSONField(
        _('Seçenekler'),
        default=dict,
        blank=True,
        help_text=_('Alan tipi için ek seçenekler')
    )
    order = models.IntegerField(
        _('Sıra'),
        default=0,
        help_text=_('Görüntüleme sırası')
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True,
        help_text=_('Bu alan aktif mi?')
    )
    show_in_list = models.BooleanField(
        _('Listede Göster'),
        default=True,
        help_text=_('Bu alan liste görünümünde gösterilsin mi?')
    )
    show_in_form = models.BooleanField(
        _('Formda Göster'),
        default=True,
        help_text=_('Bu alan form görünümünde gösterilsin mi?')
    )
    searchable = models.BooleanField(
        _('Aranabilir'),
        default=False,
        help_text=_('Bu alanda arama yapılabilsin mi?')
    )
    
    class Meta:
        verbose_name = _('Özel Alan Tanımı')
        verbose_name_plural = _('Özel Alan Tanımları')
        ordering = ['model_name', 'order', 'field_name']
        unique_together = [['model_name', 'field_name']]
    
    def __str__(self):
        return f"{self.get_model_name_display()} - {self.label}"
    
    def clean(self):
        """Validate field definition"""
        import re
        from django.core.exceptions import ValidationError
        
        # Validate field_name format
        if not re.match(r'^[a-z][a-z0-9_]*$', self.field_name):
            raise ValidationError({
                'field_name': _('Alan adı küçük harfle başlamalı ve sadece küçük harf, rakam ve alt çizgi içermelidir.')
            })
        
        # Validate options for specific field types
        if self.field_type == 'choice' and 'choices' not in self.options:
            raise ValidationError({
                'options': _('Seçim listesi alanı için seçenekler belirtilmelidir.')
            })
        
        if self.field_type == 'decimal':
            if 'max_digits' not in self.options:
                self.options['max_digits'] = 10
            if 'decimal_places' not in self.options:
                self.options['decimal_places'] = 2
    
    def get_field_instance(self):
        """Get the field type instance"""
        from core.custom_fields import CustomFieldRegistry
        field_type_class = CustomFieldRegistry.get(self.field_type)
        if field_type_class:
            return field_type_class(self)
        return None