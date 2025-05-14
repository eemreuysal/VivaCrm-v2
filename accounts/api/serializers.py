from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer for basic information."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'first_name', 'last_name',
            'title', 'department', 'phone', 'avatar', 'is_active', 'is_staff',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserDetailSerializer(UserSerializer):
    """User serializer with more detailed information."""
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['groups', 'user_permissions']


class UserCreateSerializer(serializers.ModelSerializer):
    """User serializer for creating new users."""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'title', 'department', 'phone', 'avatar', 'is_active', 'is_staff'
        ]
    
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password": "Şifreler eşleşmiyor."})
        
        # Remove password_confirm from the attributes
        attrs.pop('password_confirm', None)
        
        return attrs
    
    def validate_password(self, value):
        validate_password(value)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    current_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({"new_password": "Şifreler eşleşmiyor."})
        
        return attrs
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mevcut şifre yanlış.")
        return value
    
    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserAdminActionSerializer(serializers.Serializer):
    """Serializer for admin actions on users."""
    action = serializers.ChoiceField(choices=['toggle_active', 'toggle_staff'])
    

class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile without authentication fields."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'title', 'department', 'phone', 'avatar']