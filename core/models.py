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