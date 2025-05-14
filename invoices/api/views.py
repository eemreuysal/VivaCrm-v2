from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from invoices.models import Invoice, InvoiceItem
from invoices.services import InvoiceService
from .serializers import (
    InvoiceSerializer, InvoiceDetailSerializer, InvoiceItemSerializer,
    InvoiceCreateSerializer, InvoiceSendEmailSerializer,
    InvoiceGeneratePdfSerializer
)


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of an order or staff to access its invoices.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the order or staff
        if hasattr(obj, 'order') and hasattr(obj.order, 'owner'):
            return obj.order.owner == request.user or request.user.is_staff
        
        # For InvoiceItem, check the parent invoice
        if hasattr(obj, 'invoice') and hasattr(obj.invoice.order, 'owner'):
            return obj.invoice.order.owner == request.user or request.user.is_staff
        
        return False


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing invoices.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['order', 'invoice_type', 'status', 'is_sent']
    search_fields = ['invoice_number', 'notes', 'order__order_number', 'order__customer__name']
    ordering_fields = ['issue_date', 'due_date', 'created_at', 'total_amount']
    ordering = ['-issue_date']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'retrieve':
            return InvoiceDetailSerializer
        elif self.action == 'create' or self.action == 'create_from_order':
            return InvoiceCreateSerializer
        elif self.action == 'send_email':
            return InvoiceSendEmailSerializer
        elif self.action == 'generate_pdf':
            return InvoiceGeneratePdfSerializer
        return InvoiceSerializer
    
    def get_queryset(self):
        """
        Filter invoices based on search parameters and user permissions.
        """
        queryset = Invoice.objects.all()
        
        # Non-staff users can only see invoices for orders they own
        if not self.request.user.is_staff:
            queryset = queryset.filter(order__owner=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(issue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__lte=end_date)
        
        # Filter by amount range
        min_amount = self.request.query_params.get('min_amount', None)
        max_amount = self.request.query_params.get('max_amount', None)
        
        if min_amount:
            queryset = queryset.filter(total_amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(total_amount__lte=max_amount)
        
        # Filter by overdue status
        overdue = self.request.query_params.get('overdue', None)
        if overdue == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                due_date__lt=today,
                status__in=['draft', 'issued']
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set the created_by field to the current user if not provided.
        """
        if not serializer.validated_data.get('created_by'):
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['post'])
    def create_from_order(self, request):
        """
        Create an invoice from an order.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data.get('order').id
        invoice_type = serializer.validated_data.get('invoice_type', 'standard')
        
        from orders.models import Order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not request.user.is_staff and order.owner != request.user:
            return Response(
                {'error': 'You do not have permission to create an invoice for this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create invoice using service
        invoice = InvoiceService.create_invoice_from_order(
            order=order,
            created_by=request.user,
            invoice_type=invoice_type
        )
        
        return Response(
            InvoiceDetailSerializer(invoice, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """
        Generate a PDF for the invoice.
        """
        invoice = self.get_object()
        
        # Generate PDF using service
        html_content = InvoiceService.generate_pdf(invoice)
        
        # In a real implementation, this would generate and save a PDF file
        # For now, we just update the HTML content
        
        return Response({
            'status': 'success',
            'html_content': html_content,
            'message': 'PDF content generated'
        })
    
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """
        Send the invoice via email.
        """
        invoice = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        custom_message = serializer.validated_data.get('custom_message', '')
        
        # Send email using service
        success = InvoiceService.send_invoice_email(
            invoice=invoice,
            request=request,
            custom_message=custom_message
        )
        
        if success:
            return Response({
                'status': 'success',
                'message': 'Invoice email sent successfully'
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Failed to send invoice email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """
        Mark the invoice as paid.
        """
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.save(update_fields=['status'])
        
        # Optional: Also update the order payment status
        if invoice.order.payment_status != 'paid':
            invoice.order.payment_status = 'paid'
            invoice.order.save(update_fields=['payment_status'])
        
        return Response({
            'status': 'success',
            'message': 'Invoice marked as paid'
        })
    
    @action(detail=True, methods=['post'])
    def mark_as_issued(self, request, pk=None):
        """
        Mark the invoice as issued.
        """
        invoice = self.get_object()
        invoice.status = 'issued'
        invoice.save(update_fields=['status'])
        
        return Response({
            'status': 'success',
            'message': 'Invoice marked as issued'
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel the invoice.
        """
        invoice = self.get_object()
        invoice.status = 'cancelled'
        invoice.save(update_fields=['status'])
        
        return Response({
            'status': 'success',
            'message': 'Invoice cancelled'
        })


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing invoice items.
    """
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice']
    
    def get_queryset(self):
        """
        Filter invoice items based on user permissions.
        """
        if self.request.user.is_staff:
            return InvoiceItem.objects.all()
        
        # Non-staff users can only see items of invoices for orders they own
        return InvoiceItem.objects.filter(invoice__order__owner=self.request.user)