from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class SavedReport(models.Model):
    """
    Model to save custom reports for users.
    """
    REPORT_TYPE_CHOICES = (
        ('sales', _('Satış Raporu')),
        ('customer', _('Müşteri Raporu')),
        ('product', _('Ürün Raporu')),
        ('inventory', _('Stok Raporu')),
        ('custom', _('Özel Rapor')),
    )
    
    name = models.CharField(_("Rapor Adı"), max_length=100)
    type = models.CharField(_("Rapor Tipi"), max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Store report parameters as JSON
    parameters = models.JSONField(_("Rapor Parametreleri"), default=dict)
    
    # User who created the report
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_reports",
        verbose_name=_("Oluşturan")
    )
    
    # Is this report shared with other users?
    is_shared = models.BooleanField(_("Paylaşımlı"), default=False)
    
    # Dates
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Kaydedilmiş Rapor")
        verbose_name_plural = _("Kaydedilmiş Raporlar")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"