from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Kişisel Bilgiler"), {"fields": ("first_name", "last_name", "email", "avatar", "phone", "title", "department")}),
        (
            _("İzinler"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Önemli tarihler"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "email", "first_name", "last_name", "is_active", "is_staff"]
    search_fields = ["username", "first_name", "last_name", "email"]
    list_filter = ["is_active", "is_staff", "is_superuser"]