from rest_framework import serializers
from orders.models import Order, OrderItem, Payment, Shipment
from customers.models import Customer, Address
from products.models import Product
from products.api.serializers import ProductSimpleSerializer
from customers.api.serializers import CustomerSimpleSerializer
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class UserReferenceSerializer(serializers.ModelSerializer):
    """Simple serializer for referencing users."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class AddressReferenceSerializer(serializers.ModelSerializer):
    """Simple serializer for address references."""
    
    class Meta:
        model = Address
        fields = ['id', 'title', 'address_line1', 'city', 'country']


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    product_details = ProductSimpleSerializer(source='product', read_only=True)
    line_total = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total_with_tax = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_details', 'quantity', 
            'unit_price', 'tax_rate', 'discount_amount', 'notes',
            'line_total', 'tax_amount', 'total_with_tax'
        ]
        read_only_fields = ['id']
    
    def validate(self, attrs):
        """Validate that there is sufficient stock."""
        if self.instance is None:  # Only check on create
            product = attrs.get('product')
            quantity = attrs.get('quantity', 1)
            
            if product.stock < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Yeterli stok yok. Mevcut stok: {product.stock}'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Set unit price from product if not provided."""
        if 'unit_price' not in validated_data:
            product = validated_data.get('product')
            # Use discount_price if available, otherwise use price
            if product.discount_price and product.discount_price > 0:
                validated_data['unit_price'] = product.discount_price
            else:
                validated_data['unit_price'] = product.price
        
        if 'tax_rate' not in validated_data:
            product = validated_data.get('product')
            validated_data['tax_rate'] = product.tax_rate
        
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payments."""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'payment_method', 'amount', 'payment_date',
            'transaction_id', 'notes', 'is_successful'
        ]
        read_only_fields = ['id']


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer for shipments."""
    status_badge = serializers.ReadOnlyField(source='get_status_badge')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'order', 'carrier', 'tracking_number', 'shipping_date',
            'estimated_delivery', 'actual_delivery', 'status', 'status_display',
            'status_badge', 'notes'
        ]
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""
    customer_details = CustomerSimpleSerializer(source='customer', read_only=True)
    owner_details = UserReferenceSerializer(source='owner', read_only=True)
    status_badge = serializers.ReadOnlyField(source='get_status_badge')
    payment_status_badge = serializers.ReadOnlyField(source='get_payment_status_badge')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    payment_status_display = serializers.ReadOnlyField(source='get_payment_status_display')
    payment_method_display = serializers.ReadOnlyField(source='get_payment_method_display')
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_details', 'status', 'status_display',
            'status_badge', 'notes', 'created_at', 'updated_at', 'order_date',
            'shipping_date', 'delivery_date', 'billing_address', 'shipping_address',
            'payment_method', 'payment_method_display', 'payment_status', 
            'payment_status_display', 'payment_status_badge', 'payment_notes',
            'subtotal', 'tax_amount', 'shipping_cost', 'discount_amount',
            'total_amount', 'owner', 'owner_details', 'item_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'subtotal', 'tax_amount', 'total_amount'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()
    
    def validate(self, attrs):
        """Validate that billing and shipping addresses belong to the customer."""
        customer = attrs.get('customer', getattr(self.instance, 'customer', None))
        billing_address = attrs.get('billing_address')
        shipping_address = attrs.get('shipping_address')
        
        if billing_address and customer and billing_address.customer.id != customer.id:
            raise serializers.ValidationError({
                'billing_address': 'Bu adres seçilen müşteriye ait değil.'
            })
        
        if shipping_address and customer and shipping_address.customer.id != customer.id:
            raise serializers.ValidationError({
                'shipping_address': 'Bu adres seçilen müşteriye ait değil.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Generate order number if not provided."""
        if 'order_number' not in validated_data:
            # Simple order number generation - can be improved with a more robust approach
            import uuid
            import time
            validated_data['order_number'] = f"ORD-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}"
        
        return super().create(validated_data)


class OrderDetailSerializer(OrderSerializer):
    """Detailed serializer for order details including items, payments, and shipments."""
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    shipments = ShipmentSerializer(many=True, read_only=True)
    billing_address_details = AddressReferenceSerializer(source='billing_address', read_only=True)
    shipping_address_details = AddressReferenceSerializer(source='shipping_address', read_only=True)
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'items', 'payments', 'shipments', 
            'billing_address_details', 'shipping_address_details'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an order with items in one request."""
    items = OrderItemSerializer(many=True, required=False)
    
    class Meta:
        model = Order
        fields = [
            'order_number', 'customer', 'status', 'notes', 'order_date',
            'billing_address', 'shipping_address', 'payment_method',
            'payment_status', 'payment_notes', 'shipping_cost',
            'discount_amount', 'owner', 'items'
        ]
    
    def create(self, validated_data):
        """Create order and related items."""
        items_data = validated_data.pop('items', [])
        
        # Generate order number if not provided
        if 'order_number' not in validated_data:
            import uuid
            import time
            validated_data['order_number'] = f"ORD-{int(time.time())}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Calculate totals
        order.calculate_totals()
        
        return order


class OrderUpdateStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating order status."""
    
    class Meta:
        model = Order
        fields = ['status']


class OrderUpdatePaymentStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating order payment status."""
    
    class Meta:
        model = Order
        fields = ['payment_status']