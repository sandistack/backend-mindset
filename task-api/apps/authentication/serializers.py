from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer untuk user registration
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],  
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm')
        read_only_fields = ('id',)
    
    def validate(self, attrs):
        """
        Secure: Validate password match
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def validate_email(self, value):
        """
        Secure: Check email unique
        """
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already exists.")
        return value.lower()
    
    def validate_username(self, value):
        """
        Secure: Check username unique & format
        """
        if User.objects.filter(username=value.lower()).exists():
            raise serializers.ValidationError("Username already exists.")
        
        # Username hanya alphanumeric & underscore
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Username can only contain letters, numbers and underscores."
            )
        
        return value.lower()
    
    def create(self, validated_data):
        """
        Secure: Hash password before save
        Maintainable: Clean separation of concerns
        """
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer untuk user profile
    
    Secure: Password excluded from response
    """
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class LoginSerializer(serializers.Serializer):
    """
    Serializer untuk login validation
    
    Predictable: Clear validation errors
    """
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """
        Secure: Don't reveal if username exists
        """
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError(
                "Must include username and password."
            )
        
        return attrs