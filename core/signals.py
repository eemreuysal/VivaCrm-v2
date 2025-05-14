"""
Signal handlers for data validation and security.
"""
import logging
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.validation import validate_model_integrity
from core.security import log_security_event

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(pre_save)
def validate_before_save(sender, instance, **kwargs):
    """
    Signal handler to validate model instances before saving.
    
    This handler ensures that all model instances undergo proper validation
    before they are saved to the database, even if the validation is not
    explicitly called in the view or API.
    """
    # Skip validation for certain models or during migrations
    if kwargs.get('raw', False):  # raw is True during loaddata
        return
    
    # Skip validation for Django's built-in models
    if sender._meta.app_label in ['auth', 'contenttypes', 'sessions', 'admin',
                                 'django_celery_beat', 'django_celery_results']:
        return
    
    try:
        # Validate the model instance
        if hasattr(instance, 'full_clean'):
            instance.full_clean()
    except ValidationError as e:
        logger.error(f"Validation error in {sender.__name__} save: {str(e)}")
        raise


@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """
    Signal handler to log user account changes.
    """
    if created:
        log_security_event(
            event_type='user_created',
            description=f"User account created: {instance.username}",
            user=None,  # Creator not known from signal
            additional_data={
                'user_id': instance.id,
                'username': instance.username,
                'is_staff': instance.is_staff,
                'is_superuser': instance.is_superuser,
            }
        )
    else:
        # Check if important fields were changed
        if hasattr(instance, '_original_is_active') and instance.is_active != instance._original_is_active:
            status = "activated" if instance.is_active else "deactivated"
            log_security_event(
                event_type=f'user_{status}',
                description=f"User account {status}: {instance.username}",
                user=None,  # Modifier not known from signal
                additional_data={
                    'user_id': instance.id,
                    'username': instance.username,
                }
            )
        
        if hasattr(instance, '_original_is_staff') and instance.is_staff != instance._original_is_staff:
            action = "granted staff privileges" if instance.is_staff else "revoked staff privileges"
            log_security_event(
                event_type='user_staff_change',
                description=f"User {action}: {instance.username}",
                user=None,
                additional_data={
                    'user_id': instance.id,
                    'username': instance.username,
                }
            )


@receiver(pre_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Signal handler to log user account deletions.
    """
    log_security_event(
        event_type='user_deleted',
        description=f"User account deleted: {instance.username}",
        user=None,
        additional_data={
            'user_id': instance.id,
            'username': instance.username,
            'email': instance.email,
            'is_staff': instance.is_staff,
            'is_superuser': instance.is_superuser,
        }
    )


@receiver(pre_save, sender=User)
def store_original_values(sender, instance, **kwargs):
    """
    Store original values for fields we want to track.
    """
    if instance.pk:
        try:
            original = User.objects.get(pk=instance.pk)
            instance._original_is_active = original.is_active
            instance._original_is_staff = original.is_staff
            instance._original_is_superuser = original.is_superuser
        except User.DoesNotExist:
            pass