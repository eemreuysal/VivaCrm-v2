"""
User account management views for VivaCRM.

This module provides the views for user management functionality including:
- User profile viewing and editing
- User registration
- User listing (admin only)
- User administration (activating/deactivating, granting staff privileges)

All views implement appropriate permission checks to ensure data security.
"""

from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, UpdateView, CreateView, ListView, View
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import models

from .forms import UserChangeForm, UserCreationForm

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    """
    Display a user's profile details.
    
    This view shows the user profile with all relevant information.
    Different templates are used for staff users vs. regular users.
    """
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    
    def get_template_names(self):
        """
        Return different templates based on user permissions.
        
        Returns:
            list: Template paths to be used for rendering.
                 Admin template for staff users, regular template for others.
        """
        # Use a different template for staff users
        if self.request.user.is_staff:
            return ["accounts/admin_user_detail.html"]
        return ["accounts/user_detail.html"]
    

class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Allow users to update their profile information.
    
    This view handles the form for users to edit their own profile.
    It automatically uses the current logged-in user as the object to edit.
    """
    model = User
    form_class = UserChangeForm
    template_name = "accounts/user_form.html"
    success_message = _("Kullanıcı bilgileri başarıyla güncellendi")
    
    def get_object(self):
        """
        Return the user object to be updated (always the current user).
        
        Returns:
            User: The current logged-in user.
        """
        return self.request.user
    
    def get_success_url(self):
        """
        Determine URL to redirect to after successful update.
        
        Returns:
            str: URL to the user's detail page.
        """
        return reverse("accounts:user-detail", kwargs={"username": self.request.user.username})


class UserCreateView(SuccessMessageMixin, CreateView):
    """
    Handle new user registration.
    
    This view manages the registration form for new users.
    After successful registration, the user is automatically logged in.
    Already authenticated users are redirected to the dashboard.
    """
    model = User
    form_class = UserCreationForm
    template_name = "accounts/register.html"
    success_message = _("Hesabınız başarıyla oluşturuldu.")
    success_url = reverse_lazy('dashboard:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Handle the request and redirect authenticated users.
        
        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: Redirect or normal dispatch
        """
        # Redirect to dashboard if user is already logged in
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Process the valid form and automatically log in the user.
        
        Args:
            form: The valid form instance
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        # Automatically log in the user
        login(self.request, self.object)
        return response


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Display a list of all users (staff only).
    
    This view lists all users in the system with pagination and search functionality.
    It is restricted to staff users only through the UserPassesTestMixin.
    """
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 12
    
    def test_func(self):
        """
        Check if the current user has permission to view the list.
        
        Returns:
            bool: True if user is staff, False otherwise
        """
        # Only staff users can see the user list
        return self.request.user.is_staff
    
    def get_queryset(self):
        """
        Get the list of users with optional search filtering.
        
        Returns:
            QuerySet: Filtered user queryset
        """
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        
        if search_query:
            queryset = queryset.filter(
                models.Q(username__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query) |
                models.Q(email__icontains=search_query)
            )
            
        return queryset
        
    def get_context_data(self, **kwargs):
        """
        Add additional context for the template.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Context dictionary with additional variables
        """
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class UserAdminView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Kullanıcı yönetimi için AJAX işlevleri
    - Kullanıcı aktif/pasif yapma
    - Kullanıcıya yönetici yetkisi verme/alma
    - Kullanıcı silme
    """
    def test_func(self):
        # Sadece süper kullanıcılar bu işlemleri yapabilir
        return self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        username = kwargs.get('username')
        user = get_object_or_404(User, username=username)
        action = request.POST.get('action')
        
        if action == 'toggle_active':
            # Kullanıcıyı aktif/pasif yap
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            
            status = _('aktif') if user.is_active else _('pasif')
            messages.success(request, _(f"{user.username} kullanıcısı {status} yapıldı."))
            
        elif action == 'toggle_staff':
            # Kullanıcıya yönetici yetkisi ver/al
            user.is_staff = not user.is_staff
            user.save(update_fields=['is_staff'])
            
            status = _('yönetici yapıldı') if user.is_staff else _('yönetici yetkisi kaldırıldı')
            messages.success(request, _(f"{user.username} kullanıcısı {status}."))
            
        elif action == 'delete_user':
            # Kullanıcı kendisini silemez
            if user == request.user:
                messages.error(request, _("Kendinizi silemezsiniz."))
                return redirect('accounts:user-detail', username=username)
                
            # Kullanıcıyı sil
            username = user.username
            user.delete()
            messages.success(request, _(f"{username} kullanıcısı silindi."))
            return redirect('accounts:user-list')
        
        return redirect('accounts:user-detail', username=username)