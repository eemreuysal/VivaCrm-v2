from django.urls import path
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views
from .forms import UserLoginForm

app_name = "accounts"

urlpatterns = [
    # User management
    path("login/", LoginView.as_view(
        template_name="accounts/login.html",
        form_class=UserLoginForm
    ), name="login"),
    path("logout/", LogoutView.as_view(next_page='accounts:login'), name="logout"),
    
    # Password change
    path(
        "password-change/",
        PasswordChangeView.as_view(template_name="accounts/password_change_form.html"),
        name="password_change",
    ),
    path(
        "password-change/done/",
        PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"),
        name="password_change_done",
    ),
    
    # Password reset
    path(
        "password-reset/",
        PasswordResetView.as_view(template_name="accounts/password_reset_form.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    
    # User views
    path("register/", views.UserCreateView.as_view(), name="register"),
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("~update/", views.UserUpdateView.as_view(), name="user-update"),
    path("<str:username>/", views.UserDetailView.as_view(), name="user-detail"),
    path("<str:username>/admin-action/", views.UserAdminView.as_view(), name="user-admin-action"),
]