"""
Authentication API endpoints

Thin views: Minimal logic, delegate to services
Consistent responses: Standard format
Secure: Input validation via serializers
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .services import AuthService

import logging

logger = logging.getLogger('apps')


class RegisterView(APIView):
    """
    POST /api/auth/register/
    
    Register new user
    
    Readable: Clear endpoint purpose
    Secure: Public endpoint (AllowAny)
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Register new user
        
        Request body:
            {
                "username": "john",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!"
            }
        
        Response:
            {
                "success": true,
                "message": "User registered successfully",
                "data": {
                    "user": {...},
                    "tokens": {
                        "access": "...",
                        "refresh": "..."
                    }
                }
            }
        """
        
        # Validate input
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Call service (business logic)
            user = AuthService.register_user(
                validated_data=serializer.validated_data,
                request=request
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Return success response
            return Response({
                'success': True,
                'message': 'User registered successfully',
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            
            return Response({
                'success': False,
                'message': str(e),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    """
    POST /api/auth/login/
    
    Login user
    
    Secure: Public endpoint for login
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Login user
        
        Request body:
            {
                "username": "john",
                "password": "SecurePass123!"
            }
        
        Response:
            {
                "success": true,
                "message": "Login successful",
                "data": {
                    "user": {...},
                    "tokens": {
                        "access": "...",
                        "refresh": "..."
                    }
                }
            }
        """
        
        # Validate input
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Call service
            result = AuthService.login_user(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                request=request
            )
            
            # Return success response
            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user': UserSerializer(result['user']).data,
                    'tokens': {
                        'access': result['access'],
                        'refresh': result['refresh']
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            # Client error (invalid credentials)
            return Response({
                'success': False,
                'message': str(e),
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            # Server error
            logger.error(f"Login error: {str(e)}", exc_info=True)
            
            return Response({
                'success': False,
                'message': 'An error occurred during login',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(APIView):
    """
    GET /api/auth/profile/
    
    Get current user profile
    
    Secure: Requires authentication
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get current user profile
        
        Response:
            {
                "success": true,
                "message": "Profile retrieved successfully",
                "data": {
                    "id": 1,
                    "username": "john",
                    "email": "john@example.com",
                    "created_at": "2026-01-30T10:00:00Z"
                }
            }
        """
        
        return Response({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)