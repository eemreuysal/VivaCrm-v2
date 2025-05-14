from rest_framework import serializers
from invoices.models import Invoice, InvoiceItem
from orders.models import Order
from orders.api.serializers import OrderSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class UserReferenceSerializer(serializers.ModelSerializer):
    """Simple serializer for referencing users."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice items."""
    line_total = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total_with_tax = serializers.ReadOnlyField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'description', 'quantity', 'unit_price',
            'tax_rate', 'discount_amount', 'line_total', 'tax_amount',
            'total_with_tax'
        ]
        read_only_fields = ['id']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for invoices."""
    status_badge = serializers.ReadOnlyField(source='get_status_badge')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    invoice_type_display = serializers.ReadOnlyField(source='get_invoice_type_display')
    is_paid = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    created_by_details = UserReferenceSerializer(source='created_by', read_only=True)
    order_number = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'order', 'order_number', 'customer_name',
            'invoice_type', 'invoice_type_display', 'status', 'status_display',
            'status_badge', 'issue_date', 'due_date', 'created_at', 'updated_at',
            'subtotal', 'tax_amount', 'shipping_cost', 'discount_amount',
            'total_amount', 'pdf_file', 'html_content', 'notes', 'is_sent',
            'sent_date', 'created_by', 'created_by_details', 'is_paid', 'is_overdue'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'subtotal', 'tax_amount',
            'total_amount', 'is_sent', 'sent_date'
        ]
    
    def get_order_number(self, obj):
        return obj.order.order_number if obj.order else None
    
    def get_customer_name(self, obj):
        return obj.order.customer.name if obj.order and obj.order.customer else None


class InvoiceDetailSerializer(InvoiceSerializer):
    """Detailed serializer for invoice details including items."""
    items = InvoiceItemSerializer(many=True, read_only=True)
    order_details = OrderSerializer(source='order', read_only=True)
    
    class Meta(InvoiceSerializer.Meta):
        fields = InvoiceSerializer.Meta.fields + ['items', 'order_details']


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an invoice."""
    items = InvoiceItemSerializer(many=True, required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'order', 'invoice_type', 'status', 'issue_date',
            'due_date', 'notes', 'created_by', 'items'
        ]
    
    def create(self, validated_data):
        """Create invoice with items."""
        items_data = validated_data.pop('items', [])
        
        # Create invoice
        invoice = Invoice.objects.create(**validated_data)
        
        # Calculate amount fields from order if not provided
        order = validated_data.get('order')
        if order:
            invoice.subtotal = order.subtotal
            invoice.tax_amount = order.tax_amount
            invoice.shipping_cost = order.shipping_cost
            invoice.discount_amount = order.discount_amount
            invoice.total_amount = order.total_amount
            invoice.save(update_fields=[
                'subtotal', 'tax_amount', 'shipping_cost', 
                'discount_amount', 'total_amount'
            ])
        
        # Create invoice items
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        return invoice


class InvoiceSendEmailSerializer(serializers.Serializer):
    """Serializer for sending invoice emails."""
    custom_message = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)


class InvoiceGeneratePdfSerializer(serializers.Serializer):
    """Serializer for generating invoice PDFs."""
    pass  # No fields needed, just a marker serializer