"""
Views for authentication and user management.
"""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import User, EmailVerificationToken, PasswordResetToken, LoginHistory
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer,
    LoginHistorySerializer
)
from .services import AuthService
from .utils import get_client_ip, get_device_info
import logging

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    POST /api/v1/auth/register/
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Send verification email
        AuthService.send_verification_email(user, self.request)
        
        # Log registration
        logger.info(f"New user registered: {user.email}")
        
        return user
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please verify your email.'
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    User login endpoint.
    
    POST /api/v1/auth/login/
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
        
        # Update last login
        user.last_login = timezone.now()
        user.last_activity = timezone.now()
        user.save(update_fields=['last_login', 'last_activity'])
        
        # Record login history
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_name=get_device_info(request),
            success=True
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"User logged in: {user.email}")
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(generics.GenericAPIView):
    """
    User logout endpoint.
    
    POST /api/v1/auth/logout/
    {
        "refresh": "refresh_token_here"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logger.info(f"User logged out: {request.user.email}")
            
            return Response({'message': 'Logout successful'})
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyEmailView(generics.GenericAPIView):
    """
    Email verification endpoint.
    
    POST /api/v1/auth/verify-email/
    {
        "token": "uuid-token-here"
    }
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_uuid = serializer.validated_data['token']
        
        try:
            token = EmailVerificationToken.objects.get(token=token_uuid)
            
            if not token.is_valid():
                return Response(
                    {'error': 'Token is expired or already used'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify email
            user = token.user
            user.email_verified = True
            user.save(update_fields=['email_verified'])
            
            token.used = True
            token.save()
            
            logger.info(f"Email verified: {user.email}")
            
            return Response({'message': 'Email verified successfully'})
        
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Request password reset endpoint.
    
    POST /api/v1/auth/password-reset/
    {
        "email": "user@example.com"
    }
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            AuthService.send_password_reset_email(user, request)
            logger.info(f"Password reset requested: {email}")
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist
            pass
        
        return Response({
            'message': 'If the email exists, password reset instructions have been sent.'
        })


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirm password reset endpoint.
    
    POST /api/v1/auth/password-reset/confirm/
    {
        "token": "uuid-token-here",
        "new_password": "NewSecurePass123!",
        "new_password_confirm": "NewSecurePass123!"
    }
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_uuid = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            token = PasswordResetToken.objects.get(token=token_uuid)
            
            if not token.is_valid():
                return Response(
                    {'error': 'Token is expired or already used'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password
            user = token.user
            user.set_password(new_password)
            user.save()
            
            token.used = True
            token.save()
            
            logger.info(f"Password reset: {user.email}")
            
            return Response({'message': 'Password reset successful'})
        
        except PasswordResetToken.DoesNotExist:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    
    GET /api/v1/auth/users/ - List users
    GET /api/v1/auth/users/me/ - Get current user
    PUT /api/v1/auth/users/me/ - Update current user
    POST /api/v1/auth/users/change-password/ - Change password
    GET /api/v1/auth/users/login-history/ - Get login history
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user profile."""
        user = request.user
        
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        # Update profile
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'message': 'Password changed successfully'})
    
    @action(detail=False, methods=['get'])
    def login_history(self, request):
        """Get user login history."""
        history = LoginHistory.objects.filter(user=request.user)[:20]
        serializer = LoginHistorySerializer(history, many=True)
        return Response(serializer.data)
