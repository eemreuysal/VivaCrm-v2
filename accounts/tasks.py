from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import User


@shared_task
def send_inactive_user_notification(days=30):
    """
    Send notification emails to users who haven't logged in for a specified number of days.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    inactive_users = User.objects.filter(
        is_active=True, 
        last_login__lt=cutoff_date
    )
    
    count = 0
    for user in inactive_users:
        send_mail(
            subject="We miss you at VivaCRM!",
            message=f"Hello {user.get_full_name()},\n\nWe noticed you haven't logged into VivaCRM in a while. "
                    f"Is there anything we can help you with?\n\nBest regards,\nThe VivaCRM Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        count += 1
    
    return f"Sent {count} inactive user notifications"


@shared_task
def cleanup_inactive_users(days=90, delete=False):
    """
    Deactivate users who haven't logged in for a specified number of days.
    If delete=True, completely delete the user accounts.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    inactive_users = User.objects.filter(
        is_active=True, 
        last_login__lt=cutoff_date,
        is_staff=False,  # Never deactivate staff
        is_superuser=False  # Never deactivate superusers
    )
    
    count = 0
    if delete:
        count = inactive_users.count()
        inactive_users.delete()
        return f"Deleted {count} inactive users"
    else:
        for user in inactive_users:
            user.is_active = False
            user.save()
            count += 1
        return f"Deactivated {count} inactive users"