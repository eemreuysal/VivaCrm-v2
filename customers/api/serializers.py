from rest_framework import serializers
from customers.models import Customer, Address, Contact
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


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for customer addresses."""
    
    class Meta:
        model = Address
        fields = [
            'id', 'customer', 'title', 'type', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'is_default'
        ]
        read_only_fields = ['id']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for customer contacts."""
    
    class Meta:
        model = Contact
        fields = [
            'id', 'customer', 'name', 'title', 'department', 'email', 'phone',
            'is_primary', 'notes'
        ]
        read_only_fields = ['id']


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for customers."""
    owner_details = UserReferenceSerializer(source='owner', read_only=True)
    address_count = serializers.SerializerMethodField()
    contact_count = serializers.SerializerMethodField()
    total_orders = serializers.ReadOnlyField()
    total_revenue = serializers.ReadOnlyField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'type', 'company_name', 'tax_office', 'tax_number',
            'email', 'phone', 'website', 'notes', 'is_active', 'created_at',
            'updated_at', 'owner', 'owner_details', 'address_count', 'contact_count',
            'total_orders', 'total_revenue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_address_count(self, obj):
        return obj.addresses.count()
    
    def get_contact_count(self, obj):
        return obj.contacts.count()


class CustomerDetailSerializer(CustomerSerializer):
    """Detailed serializer for customer details including addresses and contacts."""
    addresses = AddressSerializer(many=True, read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    
    class Meta(CustomerSerializer.Meta):
        fields = CustomerSerializer.Meta.fields + ['addresses', 'contacts']


class CustomerSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for referencing customers in other contexts."""
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'type', 'company_name', 'email', 'phone']