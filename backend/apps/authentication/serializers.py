"""
MOD-01: Authentication Serializers
Handles JWT token generation with role claims + User CRUD serialization
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password
from apps.authentication.models import User, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role_id', 'role_name']


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source='role', write_only=True, required=False
    )
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            'user_id', 'full_name', 'email', 'password',
            'role', 'role_id', 'status', 'created_at'
        ]
        read_only_fields = ['user_id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)  # PBKDF2-SHA256 hash
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """Lightweight read-only serializer for embedding in other responses."""
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'role_name', 'status']

    def get_role_name(self, obj):
        return obj.role_name


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT payload — embeds role claims for frontend RBAC rendering.
    Access token includes: user_id, email, full_name, role_name
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Embed role claims for stateless frontend RBAC enforcement
        token['user_id'] = user.user_id
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role_name
        token['status'] = user.status
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Append user data to token response
        data['user'] = {
            'user_id': self.user.user_id,
            'full_name': self.user.full_name,
            'email': self.user.email,
            'role': self.user.role_name,
            'status': self.user.status,
        }
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value
