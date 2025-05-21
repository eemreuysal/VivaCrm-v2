from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Prefetch, Count, Sum
from django.utils import timezone

from products.models import (
    Category, Product, ProductImage, ProductAttribute, 
    ProductAttributeValue, StockMovement
)
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, ProductSerializer, 
    ProductDetailSerializer, ProductImageSerializer, ProductAttributeSerializer,
    ProductAttributeValueSerializer, StockMovementSerializer,
    ProductSimpleSerializer
)

try:
    from core.api_optimizations import (
        QueryOptimizationMixin, OptimizedPageNumberPagination, 
        cache_response
    )
except ImportError:
    # Fallback if optimization not available
    QueryOptimizationMixin = object
    OptimizedPageNumberPagination = None
    def cache_response(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff users to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to staff users
        return request.user and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    lookup_field = 'slug'
    
    def get_queryset(self):
        """
        Optionally restricts the returned categories by filtering against
        a `tree` query parameter in the URL.
        """
        queryset = Category.objects.all()
        tree = self.request.query_params.get('tree', None)
        
        if tree == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on parameters.
        """
        tree = self.request.query_params.get('tree', None)
        if tree == 'true':
            return CategoryTreeSerializer
        return CategorySerializer
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Return the category hierarchy as a tree.
        """
        root_categories = Category.objects.filter(parent__isnull=True)
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)


class ProductViewSet(QueryOptimizationMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing products with query optimization.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'is_featured', 'is_active', 'is_physical']
    search_fields = ['name', 'code', 'description', 'sku', 'barcode']
    ordering_fields = ['name', 'price', 'stock', 'created_at']
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    # Query optimization hints
    select_related_fields = ['category', 'family']
    prefetch_related_fields = ['images', 'attribute_values', 'stock_movements']
    
    # Use optimized pagination if available
    pagination_class = OptimizedPageNumberPagination or None
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action == 'list_simple':
            return ProductSimpleSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """
        Optionally filter the products based on query parameters.
        """
        queryset = Product.objects.all()
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock', None)
        if low_stock == 'true':
            queryset = queryset.filter(stock__lte=F('threshold_stock'))
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, slug=None):
        """
        Toggle the active status of a product.
        """
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        return Response({'status': 'product status updated'})
    
    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, slug=None):
        """
        Toggle the featured status of a product.
        """
        product = self.get_object()
        product.is_featured = not product.is_featured
        product.save()
        return Response({'status': 'product featured status updated'})
    
    @action(detail=False, methods=['get'])
    def list_simple(self, request):
        """
        Return a simplified list of products (useful for dropdowns, etc.)
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ProductSimpleSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_stock(self, request, slug=None):
        """
        Add stock to a product.
        """
        product = self.get_object()
        quantity = request.data.get('quantity', None)
        reference = request.data.get('reference', '')
        notes = request.data.get('notes', '')
        unit_cost = request.data.get('unit_cost', None)
        
        if not quantity or int(quantity) <= 0:
            return Response(
                {'error': 'A positive quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movement = StockMovement.objects.create(
            product=product,
            movement_type='purchase',
            quantity=int(quantity),
            reference=reference,
            notes=notes,
            created_by=request.user,
            unit_cost=unit_cost
        )
        
        # The actual stock update is handled by the StockMovement model's save method
        serializer = StockMovementSerializer(movement)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def remove_stock(self, request, slug=None):
        """
        Remove stock from a product.
        """
        product = self.get_object()
        quantity = request.data.get('quantity', None)
        movement_type = request.data.get('movement_type', 'adjustment')
        reference = request.data.get('reference', '')
        notes = request.data.get('notes', '')
        
        if not quantity or int(quantity) <= 0:
            return Response(
                {'error': 'A positive quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if movement_type not in ['sale', 'waste', 'adjustment', 'transfer']:
            return Response(
                {'error': 'Invalid movement type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movement = StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=int(quantity) * -1,  # Negative for stock reduction
            reference=reference,
            notes=notes,
            created_by=request.user
        )
        
        serializer = StockMovementSerializer(movement)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product images.
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'is_primary']
    ordering_fields = ['order', 'created_at']
    ordering = ['order', 'created_at']
    
    def perform_create(self, serializer):
        """
        Handle primary image: if creating a primary image, unset primary for other images.
        """
        is_primary = serializer.validated_data.get('is_primary', False)
        product = serializer.validated_data.get('product')
        
        if is_primary:
            # Remove primary status from other images
            ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
        
        serializer.save()


class ProductAttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product attributes.
    """
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']
    lookup_field = 'slug'


class ProductAttributeValueViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product attribute values.
    """
    queryset = ProductAttributeValue.objects.all()
    serializer_class = ProductAttributeValueSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'attribute']
    search_fields = ['value']
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple attribute values for a product at once.
        """
        product_id = request.data.get('product')
        attributes = request.data.get('attributes', [])
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_values = []
        
        for attr_data in attributes:
            try:
                attribute_id = attr_data.get('attribute')
                attribute = ProductAttribute.objects.get(id=attribute_id)
                value = attr_data.get('value')
                
                # Create or update the attribute value
                attr_value, created = ProductAttributeValue.objects.update_or_create(
                    product=product,
                    attribute=attribute,
                    defaults={'value': value}
                )
                
                created_values.append(attr_value)
            except ProductAttribute.DoesNotExist:
                return Response(
                    {'error': f'Attribute with ID {attribute_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = ProductAttributeValueSerializer(created_values, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing stock movements.
    """
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'movement_type', 'created_by']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Optionally filter stock movements by date range.
        """
        queryset = StockMovement.objects.all()
        
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set the created_by field to the current user.
        """
        serializer.save(created_by=self.request.user)