"""
VivaCRM core mixins.
Birden çok view'da kullanılacak mixin'ler.
"""
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class ExtendedPermissionRequiredMixin(PermissionRequiredMixin):
    """
    Varsayılan PermissionRequiredMixin'i genişletir
    Daha iyi hata mesajları, AJAX desteği ve logging ekler.
    """
    permission_error_message = _("Bu işlemi gerçekleştirmek için yetkiniz bulunmuyor.")
    permission_login_url = None
    
    def handle_no_permission(self):
        """Permission olmadığında özel davranış"""
        # Mesajı logla
        logger.warning(
            f"Permission denied: {self.request.user} tried to access "
            f"{self.request.path} without required permissions: {self.get_permission_required()}"
        )
        
        # Kullanıcıya mesaj göster
        messages.error(self.request, self.permission_error_message)
        
        # AJAX isteği ise JSON dön
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(self.permission_error_message),
                'code': 'permission_denied'
            }, status=403)
            
        # Normal behavior
        return super().handle_no_permission()
    
    def get_login_url(self):
        """Login URL için override"""
        return self.permission_login_url or super().get_login_url()


class OwnershipRequiredMixin:
    """
    Nesnenin sahibi olma kontrolü.
    Özellikle müşteri ve sipariş gibi modeller için.
    """
    owner_field = 'owner'  # Model'deki sahip alanı
    ownership_error_message = _("Bu nesne size ait değil.")
    
    def get_queryset(self):
        """Sadece kullanıcıya ait nesneleri filtrele"""
        queryset = super().get_queryset()
        
        # Eğer kullanıcı süper kullanıcı ise tüm nesneleri göster
        if self.request.user.is_superuser:
            return queryset
            
        # Aksi takdirde sadece kullanıcıya ait olanları filtrele
        return queryset.filter(**{self.owner_field: self.request.user})
    
    def has_permission(self):
        """
        Nesne sahibi mi kontrolü.
        EditView, DetailView gibi nesnelere özel view'lar için.
        """
        # Önce normal permission kontrolü
        has_perm = super().has_permission()
        if not has_perm:
            return False
            
        # Süper kullanıcı her şeyi yapabilir
        if self.request.user.is_superuser:
            return True
            
        # get_object() kullanamıyorsak (ListView vb.) varsayılan davranış
        if not hasattr(self, 'get_object'):
            return True
            
        try:
            obj = self.get_object()
            
            # Çoklu seviye attribute kontrolü (örn: order.customer.owner)
            if '.' in self.owner_field:
                parts = self.owner_field.split('.')
                value = obj
                for part in parts:
                    value = getattr(value, part)
                return value == self.request.user
                
            # Direkt attribute kontrolü
            return getattr(obj, self.owner_field) == self.request.user
            
        except (AttributeError, ValueError):
            logger.warning(
                f"Ownership check failed: {self.request.user} tried to access "
                f"{self.request.path} but object has no {self.owner_field} attribute"
            )
            return False


class TeamAccessMixin:
    """
    Takım erişim kontrolü.
    Birden fazla kullanıcının erişebildiği nesneler için.
    """
    team_field = 'team'
    team_error_message = _("Bu nesneye erişim yetkiniz yok.")
    
    def get_queryset(self):
        """Sadece kullanıcının takımlarına ait nesneleri filtrele"""
        queryset = super().get_queryset()
        
        # Eğer kullanıcı süper kullanıcı ise tüm nesneleri göster
        if self.request.user.is_superuser:
            return queryset
            
        # Kullanıcının takımlarını al
        user_teams = self.request.user.teams.all()
        
        # Takımlara ait nesneleri filtrele
        return queryset.filter(**{f"{self.team_field}__in": user_teams})


class AuditTrailMixin:
    """
    Audit trail oluştur.
    Kritik işlemleri log ve veritabanına kaydet.
    """
    
    def form_valid(self, form):
        """Form valid olduğunda audit trail oluştur"""
        response = super().form_valid(form)
        
        # Değişikliği logla
        logger.info(
            f"Audit Trail: {self.request.user} performed {self.action_type} "
            f"on {self.model.__name__} {self.object.pk}"
        )
        
        # Audit modeli varsa kaydet
        if hasattr(self, 'create_audit_trail'):
            self.create_audit_trail(form)
            
        return response
    
    def create_audit_trail(self, form):
        """Audit trail kaydı oluştur"""
        from core.models import AuditTrail
        
        changes = {}
        
        # Form'dan değişiklikleri al
        if hasattr(form, 'changed_data'):
            for field in form.changed_data:
                changes[field] = str(form.cleaned_data[field])
        
        # Audit trail kaydı oluştur
        AuditTrail.objects.create(
            user=self.request.user,
            model_name=self.model.__name__,
            object_id=self.object.pk,
            action=self.action_type,
            changes=changes
        )


class RateLimitMixin:
    """
    Rate limiting uygula.
    API ve form submission gibi işlemlerde flood koruması.
    """
    rate_limit_key = 'default'
    rate_limit_rate = '10/m'  # 10 istek/dakika
    rate_limit_error_message = _("Çok fazla istek gönderdiniz. Lütfen bir süre sonra tekrar deneyin.")
    
    def dispatch(self, request, *args, **kwargs):
        """Rate limiting uygula"""
        from django.core.cache import cache
        from django.utils import timezone
        import hashlib
        
        # Rate limit key oluştur
        cache_key = f"rate_limit:{self.rate_limit_key}:{request.user.pk}:{hashlib.md5(request.path.encode()).hexdigest()}"
        
        # Rate parse et
        count, period = self.rate_limit_rate.split('/')
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
                    'message': str(self.rate_limit_error_message),
                    'code': 'rate_limit_exceeded'
                }, status=429)
                
            # Normal istek ise mesaj göster ve yönlendir
            messages.error(request, self.rate_limit_error_message)
            return redirect('dashboard:home')
        else:
            # İstek sayısını artır
            cache.incr(cache_key)
        
        # Normal davranış
        return super().dispatch(request, *args, **kwargs)