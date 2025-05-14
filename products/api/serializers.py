from rest_framework import serializers
from products.models import Category, Product, ProductImage, ProductAttribute, ProductAttributeValue, StockMovement
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


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories."""
    product_count = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'is_active', 'created_at', 'updated_at', 'product_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']
    
    def get_product_count(self, obj):
        return obj.products.count()
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None


class CategoryTreeSerializer(CategorySerializer):
    """Serializer for categories with hierarchy."""
    children = serializers.SerializerMethodField()
    
    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['children']
    
    def get_children(self, obj):
        children = Category.objects.filter(parent=obj)
        if children:
            return CategoryTreeSerializer(children, many=True).data
        return []


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images."""
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image', 'alt_text', 'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Serializer for product attributes."""
    
    class Meta:
        model = ProductAttribute
        fields = [
            'id', 'name', 'slug', 'description', 'is_active'
        ]
        read_only_fields = ['id', 'slug']


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for product attribute values."""
    attribute_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductAttributeValue
        fields = [
            'id', 'product', 'attribute', 'attribute_name', 'value'
        ]
        read_only_fields = ['id']
    
    def get_attribute_name(self, obj):
        return obj.attribute.name


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for stock movements."""
    created_by_details = UserReferenceSerializer(source='created_by', read_only=True)
    product_name = serializers.SerializerMethodField()
    movement_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'movement_type', 'movement_type_display',
            'quantity', 'reference', 'notes', 'created_by', 'created_by_details',
            'created_at', 'previous_stock', 'new_stock', 'unit_cost'
        ]
        read_only_fields = ['id', 'created_at', 'previous_stock', 'new_stock']
    
    def get_product_name(self, obj):
        return str(obj.product)
    
    def get_movement_type_display(self, obj):
        return obj.get_movement_type_display()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products."""
    category_name = serializers.SerializerMethodField()
    tax_amount = serializers.ReadOnlyField()
    price_with_tax = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'slug', 'description', 'category', 'category_name',
            'price', 'cost', 'tax_rate', 'discount_price', 'tax_amount', 'price_with_tax',
            'profit_margin', 'stock', 'threshold_stock', 'is_physical', 'weight',
            'dimensions', 'sku', 'barcode', 'status', 'is_featured', 'is_active',
            'created_at', 'updated_at', 'primary_image'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None


class ProductDetailSerializer(ProductSerializer):
    """Detailed serializer for product details including images and attributes."""
    images = ProductImageSerializer(many=True, read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    recent_stock_movements = serializers.SerializerMethodField()
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['images', 'attribute_values', 'recent_stock_movements']
    
    def get_recent_stock_movements(self, obj):
        recent_movements = obj.stock_movements.order_by('-created_at')[:5]
        return StockMovementSerializer(recent_movements, many=True).data


class ProductSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for referencing products in other contexts."""
    
    class Meta:
        model = Product
        fields = ['id', 'code', 'name', 'price', 'discount_price', 'stock', 'status']