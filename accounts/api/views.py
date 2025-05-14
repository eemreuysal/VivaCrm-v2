from rest_framework import viewsets, permissions, status, generics, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .serializers import (
    UserSerializer, 
    UserDetailSerializer, 
    UserCreateSerializer,
    PasswordChangeSerializer,
    UserAdminActionSerializer,
    ProfileUpdateSerializer
)

User = get_user_model()


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff


class IsSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow superusers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsUserOrAdmin(permissions.BasePermission):
    """
    Allow access to a user's own details or admin users.
    """
    def has_object_permission(self, request, view, obj):
        # Allow users to access their own objects
        if obj.id == request.user.id:
            return True
        
        # Allow admin users
        return request.user.is_staff


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    lookup_field = 'username'
    
    def get_queryset(self):
        """
        This view should return a list of all users for admins
        or just the current user for non-admin users.
        """
        user = self.request.user
        
        # Non-staff users can only see themselves
        if not user.is_staff:
            return User.objects.filter(id=user.id)
        
        # Staff users can see all users
        queryset = User.objects.all().order_by('-date_joined')
        
        # Search functionality
        query = self.request.query_params.get('q', None)
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query) | 
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query)
            )
        
        # Filter by active/staff status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        is_staff = self.request.query_params.get('is_staff', None)
        if is_staff is not None:
            is_staff_bool = is_staff.lower() == 'true'
            queryset = queryset.filter(is_staff=is_staff_bool)
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve' or self.action == 'me':
            return UserDetailSerializer
        elif self.action == 'change_password':
            return PasswordChangeSerializer
        elif self.action == 'admin_action':
            return UserAdminActionSerializer
        elif self.action == 'update_profile':
            return ProfileUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsSuperUser]
        elif self.action in ['update', 'partial_update', 'destroy', 'admin_action']:
            permission_classes = [permissions.IsAuthenticated, IsUserOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns the current user's details.
        """
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change the password for the current user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        
        return Response({'detail': 'Şifre başarıyla değiştirildi.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsSuperUser])
    def admin_action(self, request, username=None):
        """
        Perform admin actions on a user (toggle active/staff status).
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        
        # Prevent modifying own account
        if user == request.user:
            return Response(
                {'detail': 'Kendi hesabınız üzerinde bu işlemi yapamazsınız.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action == 'toggle_active':
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            status_str = 'aktif' if user.is_active else 'pasif'
            message = f"{user.username} kullanıcısı {status_str} yapıldı."
        
        elif action == 'toggle_staff':
            user.is_staff = not user.is_staff
            user.save(update_fields=['is_staff'])
            status_str = 'yönetici yapıldı' if user.is_staff else 'yönetici yetkisi kaldırıldı'
            message = f"{user.username} kullanıcısı {status_str}."
        
        return Response({'detail': message}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Update current user's profile information.
        """
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)


class RegisterView(generics.CreateAPIView):
    """API endpoint for user registration."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]