"""
VivaCRM fonksiyon decorator'ları.
View ve diğer fonksiyonlar için decorator'lar.
"""
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.utils import timezone
from functools import wraps
import hashlib
import time
import logging

logger = logging.getLogger(__name__)


def ajax_required(view_func):
    """
    AJAX isteği olmayan istekleri reddeder.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Sadece AJAX istekleri kabul edilir',
                'code': 'not_ajax'
            }, status=400)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def superuser_required(view_func):
    """
    Sadece süper kullanıcıların erişebileceği view'lar için.
    """
    decorated_view = user_passes_test(
        lambda user: user.is_superuser,
        login_url='accounts:login'
    )(view_func)
    
    return decorated_view


def permission_required(perm):
    """
    Belirli bir permissiona sahip kullanıcıların erişebileceği view'lar için.
    İyi hata mesajları gösterir.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Giriş yapmış mı kontrol et
            if not request.user.is_authenticated:
                messages.error(request, _("Bu sayfaya erişmek için giriş yapmalısınız."))
                return redirect('accounts:login')
            
            # Permission var mı kontrol et
            if not request.user.has_perm(perm):
                logger.warning(
                    f"Permission denied: {request.user} tried to access "
                    f"{request.path} without required permission: {perm}"
                )
                
                messages.error(request, _("Bu işlemi gerçekleştirmek için yetkiniz bulunmuyor."))
                
                # AJAX isteği ise JSON dön
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Bu işlemi gerçekleştirmek için yetkiniz bulunmuyor.',
                        'code': 'permission_denied'
                    }, status=403)
                
                # Önceki sayfaya yönlendir veya ana sayfaya gönder
                if request.META.get('HTTP_REFERER'):
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                return redirect('dashboard:home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def ownership_required(owner_field):
    """
    Nesnenin sahibi olma kontrolü.
    Özellikle müşteri ve sipariş gibi modeller için.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Süper kullanıcı kontrolü
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # get_object fonksiyonu olmayan view'lar için
            if not hasattr(view_func, 'get_object'):
                logger.warning(
                    f"Ownership check failed: {request.user} tried to access "
                    f"{request.path} but view has no get_object method"
                )
                messages.error(request, _("Bu işlemi gerçekleştirmek için yetkiniz bulunmuyor."))
                return redirect('dashboard:home')
            
            # Nesne sahibi mi kontrol et
            try:
                obj = view_func.get_object(request, *args, **kwargs)
                
                # Çoklu seviye attribute kontrolü (örn: order.customer.owner)
                if '.' in owner_field:
                    parts = owner_field.split('.')
                    value = obj
                    for part in parts:
                        value = getattr(value, part)
                    
                    if value == request.user:
                        return view_func(request, *args, **kwargs)
                # Direkt attribute kontrolü
                elif getattr(obj, owner_field) == request.user:
                    return view_func(request, *args, **kwargs)
                
                logger.warning(
                    f"Ownership check failed: {request.user} tried to access "
                    f"{request.path} but is not owner of {obj.__class__.__name__} {obj.pk}"
                )
                
                messages.error(request, _("Bu nesne size ait değil."))
                return redirect('dashboard:home')
                
            except Exception as e:
                logger.error(
                    f"Error in ownership check: {e}",
                    exc_info=True
                )
                messages.error(request, _("Bir hata oluştu."))
                return redirect('dashboard:home')
                
        return _wrapped_view
    return decorator


def rate_limit(key, rate='10/m'):
    """
    Rate limiting uygula.
    API ve form submission gibi işlemlerde flood koruması.
    
    Args:
        key: Rate limit için unique anahtar
        rate: Rate limit formatı: [sayı]/[s,m,h,d] (saniye, dakika, saat, gün)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Anonim kullanıcılar için IP tabanlı key
            user_id = request.user.pk if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'anonymous')
            
            # Rate limit key oluştur
            path_hash = hashlib.md5(request.path.encode()).hexdigest()
            cache_key = f"rate_limit:{key}:{user_id}:{path_hash}"
            
            # Rate parse et
            count, period = rate.split('/')
            count = int(count)
            
            if period == 's':
                period_seconds = 1
            elif period == 'm':
                period_seconds = 60
            elif period == 'h':
                period_seconds = 3600
            elif period == 'd':
                period_seconds = 86400
            else:
                period_seconds = 60
            
            # Mevcut istek sayısını kontrol et
            current_requests = cache.get(cache_key)
            if current_requests is None:
                # İlk istek
                cache.set(cache_key, 1, period_seconds)
            elif current_requests >= count:
                # Rate limit aşıldı
                logger.warning(
                    f"Rate limit exceeded: {request.user} sent too many requests "
                    f"to {request.path} ({current_requests}/{count} in {period})"
                )
                
                # AJAX isteği ise JSON dön
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Çok fazla istek gönderdiniz. Lütfen bir süre sonra tekrar deneyin.',
                        'code': 'rate_limit_exceeded'
                    }, status=429)
                    
                # Normal istek ise mesaj göster ve yönlendir
                messages.error(request, _("Çok fazla istek gönderdiniz. Lütfen bir süre sonra tekrar deneyin."))
                
                if request.META.get('HTTP_REFERER'):
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                return redirect('dashboard:home')
            else:
                # İstek sayısını artır
                cache.incr(cache_key)
            
            # Normal davranış
            return view_func(request, *args, **kwargs)
            
        return _wrapped_view
    return decorator


def performance_logger(name=None):
    """
    Fonksiyon performansını ölç ve logla.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            log_name = name or view_func.__name__
            
            # Başlangıç zamanı
            start_time = time.time()
            
            # Fonksiyonu çalıştır
            result = view_func(*args, **kwargs)
            
            # Bitiş zamanı ve süre
            end_time = time.time()
            duration = end_time - start_time
            
            # Log
            if duration > 0.5:  # Sadece yavaş olanları logla
                logger.info(f"Performance: {log_name} took {duration:.4f} seconds")
            
            return result
        return _wrapped_view
    return decorator


def audit_trail(action_type):
    """
    Audit trail oluştur.
    
    Args:
        action_type: İşlem tipi (create, update, delete, etc.)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Fonksiyonu çalıştır
            result = view_func(request, *args, **kwargs)
            
            # Audit trail oluştur
            try:
                from core.models import AuditTrail
                
                # Object ID'yi bul
                object_id = None
                model_name = None
                changes = {}
                
                # CBV için
                if hasattr(view_func, 'model'):
                    model_name = view_func.model.__name__
                # FBV için
                elif hasattr(request, 'object'):
                    object_id = request.object.pk
                    model_name = request.object.__class__.__name__
                
                # Form verilerini al
                if request.method in ('POST', 'PUT'):
                    changes = dict(request.POST.items())
                    
                    # Hassas bilgileri temizle
                    for key in list(changes.keys()):
                        if 'password' in key or 'token' in key:
                            changes[key] = '******'
                
                # Audit trail kaydı oluştur
                AuditTrail.objects.create(
                    user=request.user,
                    model_name=model_name,
                    object_id=object_id,
                    action=action_type,
                    changes=changes,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                    
            except Exception as e:
                logger.error(f"Error creating audit trail: {e}", exc_info=True)
            
            return result
        return _wrapped_view
    return decorator