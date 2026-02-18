"""
Tests for Authentication API endpoints
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.authentication.models import User
from apps.tasks.factories import UserFactory


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_user_success(self, api_client):
        """Test successful user registration"""
        url = reverse('authentication:register')
        data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access' in response.data['data']['tokens']
        assert 'refresh' in response.data['data']['tokens']
        assert 'user' in response.data['data']
        assert response.data['data']['user']['email'] == 'newuser@example.com'
        
        # Verify user was created
        user = User.objects.get(email='newuser@example.com')
        assert user.name == 'New User'
        assert user.check_password('SecurePass123!')
    
    def test_register_duplicate_email(self, api_client):
        """Test registration with existing email"""
        UserFactory(email='existing@example.com')
        
        url = reverse('authentication:register')
        data = {
            'email': 'existing@example.com',
            'name': 'Test User',
            'password': 'Password123!',
            'password_confirm': 'Password123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
    
    def test_register_password_mismatch(self, api_client):
        """Test registration with mismatched passwords"""
        url = reverse('authentication:register')
        data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_missing_fields(self, api_client):
        """Test registration with missing required fields"""
        url = reverse('authentication:register')
        data = {
            'email': 'test@example.com'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data


@pytest.mark.django_db
class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_success(self, api_client):
        """Test successful login"""
        user = UserFactory(email='testuser@example.com')
        
        url = reverse('authentication:login')
        data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'  # From UserFactory
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['data']['tokens']
        assert 'refresh' in response.data['data']['tokens']
        assert 'user' in response.data['data']
        assert response.data['data']['user']['email'] == 'testuser@example.com'
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        UserFactory(email='testuser@example.com')
        
        url = reverse('authentication:login')
        data = {
            'email': 'testuser@example.com',
            'password': 'WrongPassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent user"""
        url = reverse('authentication:login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_inactive_user(self, api_client):
        """Test login with inactive user"""
        user = UserFactory(email='inactive@example.com', is_active=False)
        
        url = reverse('authentication:login')
        data = {
            'email': 'inactive@example.com',
            'password': 'TestPass123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogout:
    """Test user logout endpoint"""
    
    def test_logout_success(self, authenticated_client, user_tokens):
        """Test successful logout"""
        url = reverse('authentication:logout')
        data = {
            'refresh': user_tokens['refresh']
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_logout_unauthenticated(self, api_client):
        """Test logout without authentication"""
        url = reverse('authentication:logout')
        data = {
            'refresh': 'some_random_token'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_invalid_token(self, authenticated_client):
        """Test logout with invalid refresh token"""
        url = reverse('authentication:logout')
        data = {
            'refresh': 'invalid_token'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile endpoint (me)"""
    
    def test_get_profile_authenticated(self, authenticated_client, user):
        """Test getting current user profile"""
        url = reverse('authentication:me')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['email'] == user.email
        assert response.data['data']['name'] == user.name
        assert 'password' not in response.data
    
    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile without authentication"""
        url = reverse('authentication:me')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile(self, authenticated_client, user):
        """Test updating user profile"""
        url = reverse('authentication:me')
        data = {
            'name': 'Updated Name'
        }
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Updated Name'
        
        user.refresh_from_db()
        assert user.name == 'Updated Name'
    
    def test_update_profile_email(self, authenticated_client, user):
        """Test updating email"""
        url = reverse('authentication:me')
        data = {
            'email': 'newemail@example.com'
        }
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['email'] == 'newemail@example.com'
        
        user.refresh_from_db()
        assert user.email == 'newemail@example.com'


@pytest.mark.django_db
class TestPasswordChange:
    """Test password change endpoint"""
    
    def test_change_password_success(self, authenticated_client, user):
        """Test successful password change"""
        url = reverse('authentication:password-change')
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password('NewSecurePass123!')
    
    def test_change_password_wrong_old_password(self, authenticated_client, user):
        """Test password change with incorrect old password"""
        url = reverse('authentication:password-change')
        data = {
            'old_password': 'WrongPassword',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_mismatch(self, authenticated_client, user):
        """Test password change with mismatched new passwords"""
        url = reverse('authentication:password-change')
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPassword123!'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_unauthenticated(self, api_client):
        """Test password change without authentication"""
        url = reverse('authentication:password-change')
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPasswordReset:
    """Test password reset endpoints"""
    
    def test_request_password_reset(self, api_client):
        """Test requesting password reset"""
        user = UserFactory(email='user@example.com')
        
        url = reverse('authentication:password-reset')
        data = {
            'email': 'user@example.com'
        }
        
        response = api_client.post(url, data, format='json')
        
        # Should return success even if email doesn't exist (security)
        assert response.status_code == status.HTTP_200_OK
    
    def test_request_password_reset_nonexistent_email(self, api_client):
        """Test requesting password reset with non-existent email"""
        url = reverse('authentication:password-reset')
        data = {
            'email': 'nonexistent@example.com'
        }
        
        response = api_client.post(url, data, format='json')
        
        # Should still return success (security practice)
        assert response.status_code == status.HTTP_200_OK
