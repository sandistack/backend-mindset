from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model - for response data
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
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
        fields = ['email', 'name', 'password', 'password_confirm']
    
    def validate_email(self, value):
        """
        Check that email is unique
        """
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, attrs):
        """
        Check that passwords match
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create user with encrypted password
        """
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """
        Validate credentials and return user
        """
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,  # Django authenticate uses 'username' parameter
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials.",
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled.",
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                "Must include 'email' and 'password'.",
                code='authorization'
            )
        
        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password (authenticated user)
    """
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        write_only=True
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate_old_password(self, value):
        """
        Check that old password is correct
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """
        Check that new passwords match
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "Password fields didn't match."
            })
        return attrs
    
    def save(self):
        """
        Update user password
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        Validate that email exists
        """
        email = value.lower()
        if not User.objects.filter(email=email).exists():
            # For security, we don't tell if email exists or not
            # But we validate it here for internal processing
            pass
        return email


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset
    """
    token = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        write_only=True
    )
    password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """
        Check that passwords match
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })
        return attrs
