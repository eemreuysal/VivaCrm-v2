from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
import pandas as pd
import json
import re
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from orders.models import Order, OrderItem, Payment, Shipment
from products.models import Product, StockMovement
from customers.models import Customer, Address
from .serializers import (
    OrderSerializer, OrderDetailSerializer, OrderItemSerializer,
    PaymentSerializer, ShipmentSerializer, OrderCreateSerializer,
    OrderUpdateStatusSerializer, OrderUpdatePaymentStatusSerializer
)
from core.query_optimizer import get_optimized_queryset, log_queries
from orders.excel_validators import OrderExcelValidator
from core.excel_errors import ExcelErrorHandler
from core.excel_errors import ERROR_DEFINITIONS


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
        
        # Use optimized queryset from query_optimizer
        return get_optimized_queryset(
            queryset,
            model=Order,
            select_related=['customer', 'owner'],
            prefetch_related=['items', 'items__product', 'payments', 'shipments']
        )
    
    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """
        Bulk update order status.
        """
        order_ids = request.data.get('order_ids', [])
        new_status = request.data.get('status', None)
        
        if not order_ids or not new_status:
            return Response(
                {'error': 'order_ids and status are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orders = self.get_queryset().filter(id__in=order_ids)
        updated_count = orders.update(status=new_status, updated_at=timezone.now())
        
        return Response(
            {'message': f'{updated_count} orders updated successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        """
        Update order payment status.
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an order and restore stock.
        """
        order = self.get_object()
        
        # Check if order can be cancelled
        if order.status in ['shipped', 'delivered', 'cancelled']:
            return Response(
                {'error': 'Order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore stock
        for item in order.items.all():
            StockMovement.objects.create(
                product=item.product,
                type='in',
                quantity=item.quantity,
                reason='order_cancelled',
                reference=f'Order {order.order_number} cancelled',
                created_by=request.user
            )
            item.product.stock += item.quantity
            item.product.save()
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        return Response(
            {'message': 'Order cancelled successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate an order.
        """
        original_order = self.get_object()
        
        # Create new order
        new_order = Order.objects.create(
            customer=original_order.customer,
            owner=request.user,
            status='pending',
            payment_status='pending',
            payment_method=original_order.payment_method,
            notes=f"Duplicated from order {original_order.order_number}",
            shipping_address=original_order.shipping_address,
            billing_address=original_order.billing_address
        )
        
        # Duplicate order items
        for item in original_order.items.all():
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                tax_rate=item.tax_rate
            )
        
        # Calculate totals
        new_order.calculate_totals()
        
        # Serialize and return new order
        serializer = OrderDetailSerializer(new_order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get order statistics.
        """
        queryset = self.get_queryset()
        
        # Apply date filters
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        # Calculate statistics
        total_orders = queryset.count()
        total_revenue = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Status breakdown
        status_breakdown = queryset.values('status').annotate(
            count=models.Count('id'),
            total=Sum('total_amount')
        )
        
        # Payment status breakdown
        payment_breakdown = queryset.values('payment_status').annotate(
            count=models.Count('id'),
            total=Sum('total_amount')
        )
        
        # Top products
        top_products = OrderItem.objects.filter(
            order__in=queryset
        ).values(
            'product__id', 'product__name', 'product__code'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_revenue')[:10]
        
        # Top customers
        top_customers = queryset.values(
            'customer__id', 'customer__name', 'customer__company_name'
        ).annotate(
            total_orders=models.Count('id'),
            total_spent=Sum('total_amount')
        ).order_by('-total_spent')[:10]
        
        return Response({
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'status_breakdown': status_breakdown,
            'payment_breakdown': payment_breakdown,
            'top_products': top_products,
            'top_customers': top_customers
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export orders to Excel.
        """
        queryset = self.get_queryset()
        
        # Apply filters
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        # Create Excel file
        from orders.excel import OrderExcelExport
        export = OrderExcelExport()
        return export.export_orders(queryset)
    
    @action(detail=False, methods=['post'])
    def send_invoice(self, request):
        """
        Send invoice emails for selected orders.
        """
        order_ids = request.data.get('order_ids', [])
        
        if not order_ids:
            return Response(
                {'error': 'order_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orders = self.get_queryset().filter(id__in=order_ids)
        success_count = 0
        
        for order in orders:
            try:
                order.send_invoice_email()
                success_count += 1
            except Exception as e:
                pass
        
        return Response(
            {'message': f'{success_count} invoices sent successfully'},
            status=status.HTTP_200_OK
        )


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing order items.
    """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['order', 'product']
    search_fields = ['product__name', 'product__code']
    
    def get_queryset(self):
        """
        Filter order items based on user permissions.
        """
        return get_optimized_queryset(
            OrderItem.objects.all(),
            model=OrderItem,
            select_related=['order', 'product', 'order__customer']
        )
    
    def perform_update(self, serializer):
        """
        Update order totals after updating an order item.
        """
        instance = serializer.save()
        instance.order.calculate_totals()
    
    def perform_destroy(self, instance):
        """
        Update order totals after deleting an order item.
        """
        order = instance.order
        instance.delete()
        order.calculate_totals()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payments.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['order', 'method', 'status']
    search_fields = ['transaction_id', 'notes']
    ordering_fields = ['payment_date', 'created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter payments based on user permissions.
        """
        return get_optimized_queryset(
            Payment.objects.all(),
            model=Payment,
            select_related=['order', 'order__customer']
        )
    
    def perform_create(self, serializer):
        """
        Create payment and update order payment status.
        """
        payment = serializer.save()
        
        # Update order payment status
        order = payment.order
        total_paid = order.payments.filter(status='completed').aggregate(
            Sum('amount'))['amount__sum'] or 0
        
        if total_paid >= order.total_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partial'
        
        order.save()


class ShipmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing shipments.
    """
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['order', 'carrier', 'status']
    search_fields = ['tracking_number', 'notes']
    
    def get_queryset(self):
        """
        Filter shipments based on user permissions.
        """
        return get_optimized_queryset(
            Shipment.objects.all(),
            model=Shipment,
            select_related=['order', 'order__customer']
        )
    
    def perform_create(self, serializer):
        """
        Create shipment and update order status.
        """
        shipment = serializer.save()
        
        # Update order status
        order = shipment.order
        if shipment.status == 'delivered':
            order.status = 'delivered'
        elif shipment.status in ['shipped', 'in_transit']:
            order.status = 'shipped'
        
        order.save()


class OrderImportAPIView(APIView):
    """
    API endpoint for importing orders from Excel using the new Turkish format.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    import logging
    logger = logging.getLogger(__name__)
    
    def post(self, request):
        """
        Handle Excel file upload for order import with Turkish format.
        """
        self.logger.info("Order import API called")
        
        file = request.FILES.get('file')
        if not file:
            self.logger.error("No file uploaded")
            return Response(
                {'error': 'No file uploaded'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check file type
        if not file.name.endswith(('.xlsx', '.xls')):
            self.logger.error(f"Invalid file type: {file.name}")
            return Response(
                {'error': 'Only Excel files (.xlsx, .xls) are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            self.logger.info(f"Processing file: {file.name}")
            
            # Read Excel file
            df = pd.read_excel(file)
            self.logger.info(f"Excel columns: {df.columns.tolist()}")
            self.logger.info(f"Total rows in file: {len(df)}")
            
            # Initialize validator and error handler
            validator = OrderExcelValidator()
            error_handler = ExcelErrorHandler()
            
            # Validate file
            if not validator.validate_file(df):
                self.logger.error("File validation failed")
                errors = validator.error_collector.to_list()
                return Response(
                    {
                        'errors': errors,
                        'success': False,
                        'error_count': len(errors)
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process rows with the new format
            created_count = 0
            total_rows = len(df)
            
            # Group rows by order number
            order_groups = df.groupby("SIPARIŞ NO")
            
            for order_number, order_group in order_groups:
                try:
                    # Process only the first row for order details
                    first_row = order_group.iloc[0]
                    row_num = first_row.name + 2  # +2 because Excel is 1-indexed and we have a header row
                    
                    # Get or create customer based on name
                    customer_name = first_row["MÜŞTERI ISMI"]
                    if pd.isna(customer_name) or not customer_name:
                        error_handler.add_error(
                            'REQUIRED_FIELD', 
                            row_num, 
                            'MÜŞTERI ISMI', 
                            None,
                            extra_data={'message': 'Müşteri ismi zorunludur'}
                        )
                        continue
                    
                    # Try to find an existing customer with this name
                    customer = None
                    customers = Customer.objects.filter(name__iexact=customer_name)
                    if customers.exists():
                        customer = customers.first()
                    else:
                        # Create a valid email from customer name
                        # Remove special characters and replace spaces with dots
                        email_name = re.sub(r'[^\w\s]', '', customer_name.lower())
                        email_name = re.sub(r'\s+', '.', email_name.strip())
                        
                        # Ensure email name is not empty
                        if not email_name:
                            email_name = "customer"
                            
                        # Create a new customer if not found
                        customer = Customer.objects.create(
                            name=customer_name,
                            email=f"{email_name}@example.com",  # Placeholder email
                            phone="",  # Empty phone
                            company_name="",  # Empty company name
                            notes=f"Eyalet: {first_row.get('EYALET', '')}, Şehir: {first_row.get('ŞEHIR', '')}" if not pd.isna(first_row.get('ŞEHIR', '')) else ""
                        )
                        
                        # Create an address for the customer if we have city/state data
                        if not pd.isna(first_row.get('ŞEHIR', '')) or not pd.isna(first_row.get('EYALET', '')):
                            Address.objects.create(
                                customer=customer,
                                title="Excel Import Adresi",
                                type="shipping",
                                city=first_row.get('ŞEHIR', '') if not pd.isna(first_row.get('ŞEHIR', '')) else "",
                                state=first_row.get('EYALET', '') if not pd.isna(first_row.get('EYALET', '')) else "",
                                address_line1="Excel import'tan oluşturuldu",
                                country="Türkiye",
                                is_default=True
                            )
                    
                    # Parse order date
                    order_date_str = first_row["SIPARIŞ TARIHI VE SAATI"]
                    try:
                        # Try to parse DD.MM.YYYY HH:MM format
                        order_date = pd.to_datetime(order_date_str, format="%d.%m.%Y %H:%M")
                    except:
                        # If that fails, use pandas default parser with error handling
                        try:
                            order_date = pd.to_datetime(order_date_str)
                        except:
                            order_date = timezone.now()
                            error_handler.add_error(
                                'INVALID_DATE_FORMAT',
                                row_num,
                                'SIPARIŞ TARIHI VE SAATI',
                                order_date_str,
                                extra_data={'message': f"Geçersiz tarih formatı: {order_date_str}, varsayılan tarih kullanıldı"}
                            )
                    
                    # Prepare order notes
                    location_info = []
                    if not pd.isna(first_row.get('EYALET', '')):
                        location_info.append(first_row.get('EYALET', ''))
                    if not pd.isna(first_row.get('ŞEHIR', '')):
                        location_info.append(first_row.get('ŞEHIR', ''))
                    
                    order_notes = "Imported from Excel"
                    if location_info:
                        order_notes += f": {', '.join(location_info)}"
                    
                    # Create order
                    order = Order.objects.create(
                        order_number=order_number,
                        customer=customer,
                        status='pending',  # Default to pending
                        payment_status='pending',  # Default to pending
                        order_date=order_date,
                        notes=order_notes,
                        owner=request.user
                    )
                    
                    # Process each row in this order group to create order items
                    for idx, item_row in order_group.iterrows():
                        try:
                            item_row_num = idx + 2  # For error reporting
                            
                            # Get SKU and product name
                            sku = item_row["SKU"]
                            product_name = item_row["ÜRÜN ISMI"]
                            
                            if pd.isna(sku) or pd.isna(product_name):
                                error_handler.add_error(
                                    'REQUIRED_FIELD',
                                    item_row_num,
                                    'SKU/ÜRÜN ISMI',
                                    None,
                                    extra_data={'message': 'SKU ve ürün ismi zorunludur'}
                                )
                                continue
                            
                            # Parse quantity and price values
                            try:
                                quantity = int(item_row["ADET"])
                            except:
                                error_handler.add_error(
                                    'INVALID_NUMBER',
                                    item_row_num,
                                    'ADET',
                                    item_row['ADET'],
                                    extra_data={'message': f"Geçersiz adet: {item_row['ADET']}"}
                                )
                                continue
                            
                            # Handle comma in price (convert from European to US format)
                            unit_price_str = str(item_row["BIRIM FIYAT"]).replace(',', '.')
                            try:
                                unit_price = Decimal(unit_price_str)
                            except:
                                error_handler.add_error(
                                    'INVALID_PRICE',
                                    item_row_num,
                                    'BIRIM FIYAT',
                                    item_row['BIRIM FIYAT'],
                                    extra_data={'message': f"Geçersiz birim fiyat: {item_row['BIRIM FIYAT']}"}
                                )
                                continue
                            
                            # Handle discount if present
                            discount_amount = Decimal('0')
                            if "BIRIM INDIRIM" in item_row and not pd.isna(item_row["BIRIM INDIRIM"]):
                                discount_str = str(item_row["BIRIM INDIRIM"]).replace(',', '.')
                                try:
                                    discount_amount = Decimal(discount_str)
                                except:
                                    # If we can't parse discount, log an error but continue
                                    error_handler.add_error(
                                        'INVALID_NUMBER',
                                        item_row_num,
                                        'BIRIM INDIRIM',
                                        item_row['BIRIM INDIRIM'],
                                        extra_data={'message': f"Geçersiz indirim tutarı: {item_row['BIRIM INDIRIM']}, 0 olarak alındı"}
                                    )
                            
                            # Find or create product based on SKU
                            product = None
                            products = Product.objects.filter(sku=sku)
                            if products.exists():
                                product = products.first()
                            else:
                                # Create a new product if not found
                                product = Product.objects.create(
                                    name=product_name,
                                    sku=sku,
                                    barcode=item_row.get("GTIN", "") if not pd.isna(item_row.get("GTIN", "")) else "",
                                    description="",  # Empty description
                                    price=unit_price,
                                    discount_price=0,
                                    tax_rate=18,  # Default tax rate
                                    stock=100,  # Default stock
                                    is_active=True,
                                    code=sku  # Ensure code is set (required field)
                                )
                            
                            # Ensure decimal fields have exactly 2 decimal places
                            unit_price_decimal = unit_price.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                            discount_amount_decimal = discount_amount.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                            
                            # Create order item with properly formatted decimal values
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity,
                                unit_price=unit_price_decimal,
                                discount_amount=discount_amount_decimal,
                                tax_rate=product.tax_rate
                            )
                            
                        except Exception as e:
                            self.logger.error(f"Error processing row {item_row_num}: {e}")
                            error_handler.add_error(
                                'PROCESSING_ERROR',
                                item_row_num,
                                '',
                                '',
                                extra_data={'message': f"Sipariş kalemi hatası: {str(e)}"}
                            )
                    
                    # Calculate order totals
                    order.calculate_totals()
                    created_count += 1
                    self.logger.info(f"Created order {order.order_number}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing order {order_number}: {e}")
                    error_handler.add_error(
                        'PROCESSING_ERROR',
                        row_num,
                        '',
                        '',
                        extra_data={'message': f"Sipariş hatası: {str(e)}"}
                    )
            
            # Prepare response
            response_data = {
                'total_rows': total_rows,
                'created_count': created_count,
                'error_count': len(error_handler.errors),
                'success': created_count > 0
            }
            
            if error_handler.has_errors():
                errors_list = error_handler.to_list()
                # Limit errors to prevent huge responses
                response_data['errors'] = errors_list[:100]  # Show first 100 errors only
                if len(errors_list) > 100:
                    response_data['error_message'] = f"Showing first 100 errors out of {len(errors_list)} total errors"
            
            self.logger.info(f"Import completed: {response_data}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"Import error: {str(e)}")
            return Response(
                {'error': f'Import failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )