from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    API view for user registration
    
    POST /api/auth/register/
    {
        "email": "user@example.com",
        "name": "John Doe",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!"
    }
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Registration successful',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    API view for user login
    
    POST /api/auth/login/
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """
    API view for user logout (blacklist refresh token)
    
    POST /api/auth/logout/
    {
        "refresh": "refresh_token_here"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except TokenError:
            return Response({
                'success': False,
                'message': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    """
    API view for getting/updating current user profile
    
    GET /api/auth/me/
    PATCH /api/auth/me/
    {
        "name": "Updated Name"
    }
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'User profile retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'User profile updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class PasswordChangeView(generics.GenericAPIView):
    """
    API view for changing password (authenticated user)
    
    POST /api/auth/password-change/
    {
        "old_password": "OldPass123!",
        "new_password": "NewPass123!",
        "new_password_confirm": "NewPass123!"
    }
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(generics.GenericAPIView):
    """
    API view for requesting password reset
    
    POST /api/auth/password-reset/
    {
        "email": "user@example.com"
    }
    
    Note: For now, this prints the reset token to console.
    In production, send it via email.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # For now, print to console (in production, send email)
            reset_link = f"Token: {token}, UID: {uid}"
            print("=" * 50)
            print("PASSWORD RESET TOKEN")
            print("=" * 50)
            print(f"Email: {email}")
            print(f"UID: {uid}")
            print(f"Token: {token}")
            print("=" * 50)
            
        except User.DoesNotExist:
            # For security, don't reveal if email exists
            pass
        
        # Always return success to prevent email enumeration
        return Response({
            'success': True,
            'message': 'If the email exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API view for confirming password reset
    
    POST /api/auth/password-reset/confirm/
    {
        "uid": "encoded_user_id",
        "token": "reset_token",
        "password": "NewPass123!",
        "password_confirm": "NewPass123!"
    }
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = request.data.get('uid')
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                user.set_password(password)
                user.save()
                
                return Response({
                    'success': True,
                    'message': 'Password has been reset successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid or expired token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
