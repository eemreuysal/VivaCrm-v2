"""
Permission decorators for views.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib.auth import REDIRECT_FIELD_NAME


def permission_required(permissions, login_url=None, raise_exception=True):
    """
    Decorator for views that checks that the user has the specified permissions.
    
    Args:
        permissions: Single permission string or list of permission strings
        login_url: URL to redirect to on permission failure
        raise_exception: Whether to raise PermissionDenied (True) or redirect (False)
    """
    if isinstance(permissions, str):
        permissions = [permissions]
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser or request.user.has_perms(permissions):
                    return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            else:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(
                    request.get_full_path(),
                    login_url,
                    redirect_field_name=REDIRECT_FIELD_NAME
                )
        return wrapper
    return decorator