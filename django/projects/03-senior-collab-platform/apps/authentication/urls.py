"""
URL routing for authentication endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # JWT Token
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Email Verification
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    
    # Password Reset
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User Management
    path('', include(router.urls)),
]
