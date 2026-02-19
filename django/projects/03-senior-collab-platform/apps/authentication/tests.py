"""
Tests for authentication app.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for testing."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='TestPass123!',
        first_name='Test',
        last_name='User'
    )


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for user registration."""
    
    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post('/api/v1/auth/register/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == data['email']
    
    def test_register_duplicate_email(self, api_client, test_user):
        """Test registration with existing email fails."""
        data = {
            'email': test_user.email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'Duplicate'
        }
        response = api_client.post('/api/v1/auth/register/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Tests for user login."""
    
    def test_login_success(self, api_client, test_user):
        """Test successful login."""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = api_client.post('/api/v1/auth/login/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert 'user' in response.data
    
    def test_login_invalid_credentials(self, api_client, test_user):
        """Test login with invalid credentials fails."""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        response = api_client.post('/api/v1/auth/login/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfile:
    """Tests for user profile."""
    
    def test_get_profile(self, api_client, test_user):
        """Test getting user profile."""
        api_client.force_authenticate(user=test_user)
        response = api_client.get('/api/v1/auth/users/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == test_user.email
    
    def test_update_profile(self, api_client, test_user):
        """Test updating user profile."""
        api_client.force_authenticate(user=test_user)
        data = {'first_name': 'Updated'}
        response = api_client.patch('/api/v1/auth/users/me/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
