from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from customers.models import Customer, Address, Contact
from .serializers import (
    CustomerSerializer, 
    CustomerDetailSerializer,
    AddressSerializer,
    ContactSerializer
)
from core.query_optimizer import get_optimized_queryset, log_queries


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners or staff to edit.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner or staff
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.is_staff
        
        # For related objects, check customer ownership
        if hasattr(obj, 'customer') and hasattr(obj.customer, 'owner'):
            return obj.customer.owner == request.user or request.user.is_staff
        
        return False


class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing customers.
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active', 'owner']
    search_fields = ['name', 'company_name', 'email', 'phone', 'tax_number']
    ordering_fields = ['name', 'created_at', 'updated_at', 'type']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CustomerDetailSerializer
        return CustomerSerializer
    
    @log_queries
    def get_queryset(self):
        """
        Filter customers based on search parameters and user permissions.
        Returns an optimized queryset with select_related and prefetch_related.
        """
        queryset = Customer.objects.all()
        
        # Non-staff users can only see customers they own
        if not self.request.user.is_staff:
            queryset = queryset.filter(Q(owner=self.request.user) | Q(owner__isnull=True))
        
        # Filter by search query
        query = self.request.query_params.get('q', None)
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(company_name__icontains=query) | 
                Q(email__icontains=query) | 
                Q(phone__icontains=query) | 
                Q(tax_number__icontains=query)
            )
        
        # Apply optimizations based on the action
        if self.action == 'retrieve':
            # For detail views, prefetch related data
            queryset = get_optimized_queryset('Customer', queryset)
        elif self.action == 'list':
            # For list views, only select related owner
            queryset = queryset.select_related('owner')
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set the owner to the current user if not provided.
        """
        if not serializer.validated_data.get('owner'):
            serializer.save(owner=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive (deactivate) a customer.
        """
        customer = self.get_object()
        customer.is_active = False
        customer.save()
        return Response({'status': 'customer archived'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a customer.
        """
        customer = self.get_object()
        customer.is_active = True
        customer.save()
        return Response({'status': 'customer activated'})


class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing customer addresses.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer', 'type', 'is_default', 'city', 'country']
    ordering_fields = ['title', 'city', 'is_default']
    ordering = ['-is_default', 'title']
    
    @log_queries
    def get_queryset(self):
        """
        Filter addresses based on user permissions.
        Returns an optimized queryset with select_related.
        """
        queryset = Address.objects.select_related('customer', 'customer__owner')
        
        if self.request.user.is_staff:
            return queryset
        
        # Non-staff users can only see addresses of customers they own
        return queryset.filter(customer__owner=self.request.user)
    
    def perform_create(self, serializer):
        """
        Handle default status: if creating a default address, unset default for other addresses.
        """
        is_default = serializer.validated_data.get('is_default', False)
        customer = serializer.validated_data.get('customer')
        
        if is_default and customer:
            # Remove default status from other addresses
            Address.objects.filter(customer=customer, is_default=True).update(is_default=False)
        
        serializer.save()


class ContactViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing customer contacts.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'is_primary', 'department']
    search_fields = ['name', 'email', 'phone', 'title', 'department']
    ordering_fields = ['name', 'is_primary']
    ordering = ['-is_primary', 'name']
    
    @log_queries
    def get_queryset(self):
        """
        Filter contacts based on user permissions.
        Returns an optimized queryset with select_related.
        """
        queryset = Contact.objects.select_related('customer', 'customer__owner')
        
        if self.request.user.is_staff:
            return queryset
        
        # Non-staff users can only see contacts of customers they own
        return queryset.filter(customer__owner=self.request.user)
    
    def perform_create(self, serializer):
        """
        Handle primary status: if creating a primary contact, unset primary for other contacts.
        """
        is_primary = serializer.validated_data.get('is_primary', False)
        customer = serializer.validated_data.get('customer')
        
        if is_primary and customer:
            # Remove primary status from other contacts
            Contact.objects.filter(customer=customer, is_primary=True).update(is_primary=False)
        
        serializer.save()