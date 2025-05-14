from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404

from orders.models import Order, OrderItem, Payment, Shipment
from products.models import Product, StockMovement
from .serializers import (
    OrderSerializer, OrderDetailSerializer, OrderItemSerializer,
    PaymentSerializer, ShipmentSerializer, OrderCreateSerializer,
    OrderUpdateStatusSerializer, OrderUpdatePaymentStatusSerializer
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
        
        # For related objects, check order ownership
        if hasattr(obj, 'order') and hasattr(obj.order, 'owner'):
            return obj.order.owner == request.user or request.user.is_staff
        
        return False


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing orders.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'status', 'payment_status', 'payment_method', 'owner']
    search_fields = ['order_number', 'notes', 'customer__name', 'customer__company_name']
    ordering_fields = ['order_date', 'created_at', 'updated_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'retrieve':
            return OrderDetailSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'update_status':
            return OrderUpdateStatusSerializer
        elif self.action == 'update_payment_status':
            return OrderUpdatePaymentStatusSerializer
        return OrderSerializer
    
    @log_queries
    def get_queryset(self):
        """
        Filter orders based on search parameters and user permissions.
        Returns an optimized queryset with select_related and prefetch_related.
        """
        queryset = Order.objects.all()
        
        # Non-staff users can only see orders they own
        if not self.request.user.is_staff:
            queryset = queryset.filter(Q(owner=self.request.user) | Q(owner__isnull=True))
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        # Filter by amount range
        min_amount = self.request.query_params.get('min_amount', None)
        max_amount = self.request.query_params.get('max_amount', None)
        
        if min_amount:
            queryset = queryset.filter(total_amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(total_amount__lte=max_amount)
        
        # Apply optimizations based on the action
        if self.action == 'retrieve':
            # For detail views, prefetch all related data
            queryset = get_optimized_queryset('Order', queryset)
        elif self.action == 'list':
            # For list views, only select related customer and owner
            queryset = queryset.select_related('customer', 'owner')
        
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
    def update_status(self, request, pk=None):
        """
        Update order status.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # If order is completed, reduce stock
        if serializer.validated_data.get('status') == 'completed' and order.status != 'completed':
            self._reduce_stock(order)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        """
        Update order payment status.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """
        Add a payment to an order.
        """
        order = self.get_object()
        
        # Create payment serializer
        payment_serializer = PaymentSerializer(data=request.data)
        payment_serializer.is_valid(raise_exception=True)
        payment = payment_serializer.save(order=order)
        
        # Update order payment status
        total_paid = order.payments.filter(is_successful=True).aggregate(total=Sum('amount'))['total'] or 0
        
        if total_paid >= order.total_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partially_paid'
        else:
            order.payment_status = 'pending'
            
        order.save(update_fields=['payment_status'])
        
        return Response(payment_serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_shipment(self, request, pk=None):
        """
        Add a shipment to an order.
        """
        order = self.get_object()
        
        # Create shipment serializer
        shipment_serializer = ShipmentSerializer(data=request.data)
        shipment_serializer.is_valid(raise_exception=True)
        shipment = shipment_serializer.save(order=order)
        
        # Update order shipping date if not set
        if not order.shipping_date and shipment.status in ['shipped', 'in_transit']:
            order.shipping_date = shipment.shipping_date
            order.status = 'shipped'
            order.save(update_fields=['shipping_date', 'status'])
        
        # Update order delivery date if shipment is delivered
        if shipment.status == 'delivered' and shipment.actual_delivery:
            order.delivery_date = shipment.actual_delivery
            order.status = 'delivered'
            order.save(update_fields=['delivery_date', 'status'])
        
        return Response(shipment_serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an order.
        """
        order = self.get_object()
        
        # Can only cancel orders that are not completed, delivered or already cancelled
        if order.status in ['completed', 'delivered', 'cancelled', 'refunded']:
            return Response(
                {'error': f'Sipariş şu anda {order.get_status_display()} durumunda ve iptal edilemez.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        order.status = 'cancelled'
        order.payment_status = 'cancelled'
        order.save(update_fields=['status', 'payment_status'])
        
        return Response({'status': 'order cancelled'})
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Refund an order.
        """
        order = self.get_object()
        
        # Can only refund orders that are completed or delivered
        if order.status not in ['completed', 'delivered']:
            return Response(
                {'error': f'Sipariş şu anda {order.get_status_display()} durumunda ve iade edilemez.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        order.status = 'refunded'
        order.payment_status = 'refunded'
        order.save(update_fields=['status', 'payment_status'])
        
        return Response({'status': 'order refunded'})
    
    def _reduce_stock(self, order):
        """
        Reduce stock for all items in the order.
        Creates StockMovement records for each item.
        """
        items = order.items.all()
        
        for item in items:
            # Create stock movement
            StockMovement.objects.create(
                product=item.product,
                movement_type='sale',
                quantity=-item.quantity,  # Negative for reduction
                reference=f"Sipariş #{order.order_number}",
                notes=f"Otomatik stok düşümü - {item.quantity} adet",
                created_by=self.request.user
            )
            # Note: The actual stock update is handled by the StockMovement model's save method


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing order items.
    """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'product']
    
    @log_queries
    def get_queryset(self):
        """
        Filter order items based on user permissions.
        Returns an optimized queryset with select_related.
        """
        queryset = OrderItem.objects.select_related('order', 'order__owner', 'product')
        
        if self.request.user.is_staff:
            return queryset
        
        # Non-staff users can only see items of orders they own
        return queryset.filter(order__owner=self.request.user)
    
    def perform_create(self, serializer):
        """
        After saving the item, recalculate order totals.
        """
        item = serializer.save()
        item.order.calculate_totals()
    
    def perform_update(self, serializer):
        """
        After updating the item, recalculate order totals.
        """
        item = serializer.save()
        item.order.calculate_totals()
    
    def perform_destroy(self, instance):
        """
        Before deleting the item, keep reference to the order.
        """
        order = instance.order
        super().perform_destroy(instance)
        # Recalculate order totals after item is deleted
        order.calculate_totals()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payments.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'payment_method', 'is_successful']
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']
    
    @log_queries
    def get_queryset(self):
        """
        Filter payments based on user permissions.
        Returns an optimized queryset with select_related.
        """
        queryset = Payment.objects.select_related('order', 'order__owner', 'order__customer')
        
        if self.request.user.is_staff:
            return queryset
        
        # Non-staff users can only see payments of orders they own
        return queryset.filter(order__owner=self.request.user)
    
    def perform_create(self, serializer):
        """
        After saving the payment, update order payment status.
        """
        payment = serializer.save()
        order = payment.order
        
        # Calculate total paid
        total_paid = order.payments.filter(is_successful=True).aggregate(total=Sum('amount'))['total'] or 0
        
        # Update order payment status
        if total_paid >= order.total_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partially_paid'
        else:
            order.payment_status = 'pending'
            
        order.save(update_fields=['payment_status'])
    
    def perform_update(self, serializer):
        """
        After updating the payment, update order payment status.
        """
        self.perform_create(serializer)  # Reuse the same logic
    
    def perform_destroy(self, instance):
        """
        Before deleting the payment, keep reference to the order.
        """
        order = instance.order
        super().perform_destroy(instance)
        
        # Recalculate total paid and update order status
        total_paid = order.payments.filter(is_successful=True).aggregate(total=Sum('amount'))['total'] or 0
        
        if total_paid >= order.total_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partially_paid'
        else:
            order.payment_status = 'pending'
            
        order.save(update_fields=['payment_status'])


class ShipmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing shipments.
    """
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'carrier', 'status']
    ordering_fields = ['shipping_date']
    ordering = ['-shipping_date']
    
    @log_queries
    def get_queryset(self):
        """
        Filter shipments based on user permissions.
        Returns an optimized queryset with select_related.
        """
        queryset = Shipment.objects.select_related('order', 'order__owner', 'order__customer')
        
        if self.request.user.is_staff:
            return queryset
        
        # Non-staff users can only see shipments of orders they own
        return queryset.filter(order__owner=self.request.user)
    
    def perform_create(self, serializer):
        """
        After saving the shipment, update order status.
        """
        shipment = serializer.save()
        order = shipment.order
        
        # Update order shipping date if not set
        if not order.shipping_date and shipment.status in ['shipped', 'in_transit']:
            order.shipping_date = shipment.shipping_date
            order.status = 'shipped'
            order.save(update_fields=['shipping_date', 'status'])
        
        # Update order delivery date if shipment is delivered
        if shipment.status == 'delivered' and shipment.actual_delivery:
            order.delivery_date = shipment.actual_delivery
            order.status = 'delivered'
            order.save(update_fields=['delivery_date', 'status'])
    
    def perform_update(self, serializer):
        """
        After updating the shipment, update order status.
        """
        previous_status = self.get_object().status
        shipment = serializer.save()
        order = shipment.order
        
        # If status changed to shipped or in_transit, update order
        if previous_status not in ['shipped', 'in_transit'] and shipment.status in ['shipped', 'in_transit']:
            if not order.shipping_date:
                order.shipping_date = shipment.shipping_date
                order.status = 'shipped'
                order.save(update_fields=['shipping_date', 'status'])
        
        # If status changed to delivered, update order
        if previous_status != 'delivered' and shipment.status == 'delivered':
            if shipment.actual_delivery:
                order.delivery_date = shipment.actual_delivery
                order.status = 'delivered'
                order.save(update_fields=['delivery_date', 'status'])