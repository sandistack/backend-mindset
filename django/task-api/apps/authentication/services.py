# apps/authentication/services.py
"""
Authentication business logic

Maintainable: Separate business logic from views
Testable: Can be tested without HTTP requests
Secure: Centralized security logic
"""

from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.utils import log_activity
import logging

User = get_user_model()
logger = logging.getLogger('apps')


class AuthService:
    """
    Service untuk handle authentication logic
    
    Single Responsibility: Hanya handle auth
    Predictable: Consistent behavior
    """
    
    @staticmethod
    def register_user(validated_data, request=None):
        """
        Register new user
        
        Args:
            validated_data: Dict dari RegisterSerializer
            request: HTTP request object (optional)
        
        Returns:
            User instance
        
        Raises:
            Exception: If registration fails
        
        Secure: Password already validated by serializer
        Maintainable: Single place for registration logic
        """
        try:
            logger.info(f"Attempting to register user: {validated_data.get('email')}")
            
            # Create user (password will be hashed)
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )
            
            logger.info(f"User registered successfully: {user.email}")
            
            # Log to audit trail
            log_activity(
                user=user,
                action='CREATE',
                feature='user',
                description=f"User registered: {user.username}",
                request=request,
                status='SUCCESS'
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}", exc_info=True)
            
            # Log error
            log_activity(
                user=None,
                action='ERROR',
                feature='user',
                description=f"Registration failed: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise
    
    @staticmethod
    def login_user(username, password, request=None):
        """
        Authenticate user and generate JWT tokens
        
        Args:
            username: Username or email
            password: User password
            request: HTTP request object (optional)
        
        Returns:
            Dict with user and tokens
        
        Raises:
            ValueError: If credentials invalid
        
        Secure: Password check via Django auth
        Predictable: Clear error messages
        """
        try:
            logger.info(f"Login attempt: {username}")
            
            # Authenticate
            user = authenticate(username=username, password=password)
            
            if not user:
                logger.warning(f"Login failed - invalid credentials: {username}")
                
                # Log failed attempt
                log_activity(
                    user=None,
                    action='ERROR',
                    feature='authentication',
                    description=f"Login failed - invalid credentials: {username}",
                    request=request,
                    status='FAILED'
                )
                
                raise ValueError("Invalid credentials")
            
            if not user.is_active:
                logger.warning(f"Login failed - inactive user: {username}")
                
                log_activity(
                    user=user,
                    action='ERROR',
                    feature='authentication',
                    description=f"Login failed - inactive account",
                    request=request,
                    status='FAILED'
                )
                
                raise ValueError("Account is inactive")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            logger.info(f"Login successful: {user.username}")
            
            # Log successful login
            log_activity(
                user=user,
                action='CREATE',
                feature='authentication',
                description=f"User logged in successfully",
                request=request,
                status='SUCCESS'
            )
            
            return {
                'user': user,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            
            log_activity(
                user=None,
                action='ERROR',
                feature='authentication',
                description=f"Login error: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise