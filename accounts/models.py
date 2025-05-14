from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model for VivaCRM.
    Extends Django's AbstractUser to add additional fields.
    """
    email = models.EmailField(_("Email adresi"), unique=True)
    avatar = models.ImageField(_("Profil resmi"), upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(_("Telefon"), max_length=15, blank=True)
    title = models.CharField(_("Unvan"), max_length=100, blank=True)
    department = models.CharField(_("Departman"), max_length=100, blank=True)
    is_active = models.BooleanField(
        _("Aktif"),
        default=True,
        help_text=_(
            "Kullanıcının aktif olup olmadığını belirtir. "
            "Kullanıcıyı silmek yerine bunu kaldırın."
        ),
    )
    
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("Kullanıcı")
        verbose_name_plural = _("Kullanıcılar")
        
    def get_absolute_url(self):
        return reverse("accounts:user-detail", kwargs={"username": self.username})
        
    def __str__(self):
        return self.get_full_name() or self.username