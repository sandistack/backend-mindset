"""
Pytest configuration and shared fixtures
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    """
    Return an API client instance
    """
    return APIClient()


@pytest.fixture
def user(db):
    """
    Create a regular user for testing
    """
    return User.objects.create_user(
        email='testuser@example.com',
        name='Test User',
        password='TestPass123!'
    )


@pytest.fixture
def another_user(db):
    """
    Create another user for testing permissions
    """
    return User.objects.create_user(
        email='another@example.com',
        name='Another User',
        password='TestPass123!'
    )


@pytest.fixture
def superuser(db):
    """
    Create a superuser for testing
    """
    return User.objects.create_superuser(
        email='admin@example.com',
        name='Admin User',
        password='AdminPass123!'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """
    Return an API client authenticated with a user
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user_tokens(user):
    """
    Generate JWT tokens for a user
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


@pytest.fixture
def authenticated_client_with_token(api_client, user, user_tokens):
    """
    Return an API client authenticated with JWT token in header
    """
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {user_tokens['access']}")
    return api_client
