from django.db import models
from django.utils.translation import gettext_lazy as _

class SystemSettings(models.Model):
    """
    Model for storing system-wide settings.
    Uses a key-value pattern to store different settings.
    """
    CATEGORY_CHOICES = (
        ('general', _('Genel')),
        ('email', _('E-posta')),
        ('advanced', _('Gelişmiş')),
        ('security', _('Güvenlik')),
    )
    
    key = models.CharField(_("Anahtar"), max_length=100, unique=True)
    value = models.TextField(_("Değer"))
    description = models.CharField(_("Açıklama"), max_length=255, blank=True)
    category = models.CharField(_("Kategori"), max_length=50, choices=CATEGORY_CHOICES, default='general')
    is_public = models.BooleanField(_("Herkese Açık"), default=True, 
                                   help_text=_("Public settings are visible to all authenticated users"))
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Sistem Ayarı")
        verbose_name_plural = _("Sistem Ayarları")
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.key} ({self.get_category_display()})"
    
    @classmethod
    def get_setting(cls, key, default=None):
        """
        Get a setting value by key
        """
        try:
            setting = cls.objects.get(key=key)
            return setting.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, category='general', description='', is_public=True):
        """
        Set a setting value (create or update)
        """
        setting, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'category': category,
                'description': description,
                'is_public': is_public
            }
        )
        return setting
