"""
Test cases for user views using pytest and model_bakery
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from model_bakery import baker

from apps.users.models import UserInterest

User = get_user_model()


@pytest.fixture
def api_client():
    """Create an API client for testing"""
    return APIClient()


@pytest.fixture
def create_user():
    """Factory to create users with model_bakery"""
    def make_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'regular',
            'is_active': True,
        }
        defaults.update(kwargs)
        user = baker.make(User, **defaults)
        if 'password' in kwargs:
            user.set_password(kwargs['password'])
            user.save()
        return user
    return make_user


@pytest.fixture
def authenticated_client(api_client, create_user):
    """Create an authenticated API client"""
    user = create_user(password='testpass123')
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = user
    return api_client


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_user_registration_success(self, api_client):
        """Test successful user registration with all required fields"""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'regular',
            'bio': 'Test bio for new user'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['username'] == 'newuser'
        assert response.data['user']['email'] == 'newuser@example.com'
        assert response.data['message'] == 'Registration successful. You are now logged in.'
        
        # Verify user was created in database
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.bio == 'Test bio for new user'
        assert user.check_password('StrongPass123!')
    
    def test_user_registration_with_interests(self, api_client):
        """Test user registration with interests"""
        url = reverse('user-register')
        data = {
            'username': 'userinterests',
            'email': 'interests@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Interest',
            'last_name': 'User',
            'interests': ['Technology', 'Science', 'Politics']
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(username='userinterests')
        interests = UserInterest.objects.filter(user=user)
        assert interests.count() == 3
        interest_names = [i.name for i in interests]
        assert 'Technology' in interest_names
        assert 'Science' in interest_names
        assert 'Politics' in interest_names
    
    def test_user_registration_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match"""
        url = reverse('user-register')
        data = {
            'username': 'failuser',
            'email': 'fail@example.com',
            'password': 'StrongPass123!',
            'password2': 'DifferentPass123!',
            'first_name': 'Fail',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # The error is wrapped in the general error response
        assert 'error' in response.data
        assert 'Registration failed' in response.data['error']
        assert User.objects.filter(username='failuser').exists() is False


@pytest.mark.django_db
class TestUserAuthentication:
    """Test user authentication functionality"""
    
    def test_user_login_success(self, api_client, create_user):
        """Test successful login with correct credentials"""
        user = create_user(
            username='loginuser',
            email='login@example.com',
            password='correctpass123',
            user_type='editor',
            is_verified=True
        )
        
        url = reverse('user-login')
        data = {
            'username': 'loginuser',
            'password': 'correctpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['username'] == 'loginuser'
        assert response.data['email'] == 'login@example.com'
        assert response.data['user_type'] == 'editor'
        assert response.data['is_verified'] is True
    
    def test_user_login_invalid_password(self, api_client, create_user):
        """Test login fails with incorrect password"""
        create_user(
            username='loginuser',
            password='correctpass123'
        )
        
        url = reverse('user-login')
        data = {
            'username': 'loginuser',
            'password': 'wrongpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'access' not in response.data
    
    def test_token_refresh_success(self, api_client, create_user):
        """Test token refresh works correctly"""
        user = create_user(password='testpass123')
        refresh = RefreshToken.for_user(user)
        
        url = reverse('token-refresh')
        data = {'refresh': str(refresh)}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile functionality"""
    
    def test_get_current_user_profile(self, authenticated_client):
        """Test getting current user's profile"""
        url = reverse('user-me')
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == authenticated_client.user.username
        assert response.data['email'] == authenticated_client.user.email
        assert 'interests' in response.data
    
    def test_update_current_user_profile(self, authenticated_client):
        """Test updating current user's profile"""
        url = reverse('user-update-me')
        data = {
            'bio': 'Updated bio text',
            'location': 'New York, USA',
            'website': 'https://example.com',
            'twitter': '@testuser',
            'linkedin': 'testuser'
        }
        
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bio'] == 'Updated bio text'
        assert response.data['location'] == 'New York, USA'
        assert response.data['website'] == 'https://example.com'
        assert response.data['twitter'] == '@testuser'
        assert response.data['linkedin'] == 'testuser'
        
        # Verify database update
        user = User.objects.get(id=authenticated_client.user.id)
        assert user.bio == 'Updated bio text'
        assert user.location == 'New York, USA'
    
    def test_partial_update_user_profile(self, authenticated_client):
        """Test partial update (PATCH) of user profile"""
        url = reverse('user-update-me')
        data = {'bio': 'Only bio updated'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bio'] == 'Only bio updated'
        
        # Other fields should remain unchanged
        user = User.objects.get(id=authenticated_client.user.id)
        assert user.bio == 'Only bio updated'
        assert user.username == authenticated_client.user.username
    
    def test_change_password_success(self, authenticated_client):
        """Test changing password with correct old password"""
        url = reverse('user-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewStrongPass123!'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Password changed successfully.'
        
        # Verify new password works
        user = User.objects.get(id=authenticated_client.user.id)
        assert user.check_password('NewStrongPass123!')
        assert not user.check_password('testpass123')
    
    def test_change_password_wrong_old_password(self, authenticated_client):
        """Test change password fails with incorrect old password"""
        url = reverse('user-change-password')
        data = {
            'old_password': 'wrongoldpass',
            'new_password': 'NewStrongPass123!'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Old password is incorrect.'
        
        # Verify password unchanged
        user = User.objects.get(id=authenticated_client.user.id)
        assert user.check_password('testpass123')
    
    def test_change_password_missing_fields(self, authenticated_client):
        """Test change password fails when fields are missing"""
        url = reverse('user-change-password')
        data = {'old_password': 'testpass123'}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Both old_password and new_password are required.'


@pytest.mark.django_db
class TestUserListAndSearch:
    """Test user listing and search functionality"""
    
    def test_list_users_public(self, api_client, create_user):
        """Test listing users without authentication"""
        # Create multiple users
        baker.make(User, _quantity=3)
        create_user(username='publicuser')
        
        url = reverse('user-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 4
        # Should use minimal serializer for public access
        assert 'email' not in response.data['results'][0]
    
    def test_search_users_by_username(self, api_client, create_user):
        """Test searching users by username"""
        create_user(username='johnsmith', first_name='John', last_name='Smith')
        create_user(username='janedoe', first_name='Jane', last_name='Doe')
        create_user(username='testjohn', first_name='Test', last_name='John')
        
        url = reverse('user-list')
        response = api_client.get(url, {'search': 'john'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 2
        usernames = [u['username'] for u in response.data['results']]
        assert 'johnsmith' in usernames
        assert 'testjohn' in usernames
    
    def test_search_users_by_name(self, api_client, create_user):
        """Test searching users by first or last name"""
        create_user(username='user1', first_name='Michael', last_name='Jordan')
        create_user(username='user2', first_name='Sarah', last_name='Michael')
        
        url = reverse('user-list')
        response = api_client.get(url, {'search': 'Michael'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 2
        
    def test_filter_users_by_type(self, api_client):
        """Test filtering users by user type"""
        baker.make(User, user_type='journalist', _quantity=2)
        baker.make(User, user_type='editor', _quantity=3)
        baker.make(User, user_type='regular', _quantity=1)
        
        url = reverse('user-list')
        response = api_client.get(url, {'user_type': 'editor'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert all(u['user_type'] == 'editor' for u in response.data['results'])
    
    def test_get_user_detail_public(self, api_client, create_user):
        """Test getting user detail without authentication"""
        user = create_user(
            username='detailuser',
            bio='Public bio',
            location='London',
            is_verified=True
        )
        
        url = reverse('user-detail', kwargs={'pk': user.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'detailuser'
        assert response.data['bio'] == 'Public bio'
        assert response.data['location'] == 'London'
        assert response.data['is_verified'] is True
    
    def test_user_search_endpoint(self, api_client, create_user):
        """Test dedicated search endpoint"""
        create_user(username='searchtest1', first_name='Alice')
        create_user(username='searchtest2', first_name='Bob')
        
        url = reverse('user-search')
        response = api_client.get(url, {'q': 'Alice'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert response.data['results'][0]['first_name'] == 'Alice'
    
    def test_user_search_empty_query(self, api_client):
        """Test search with empty query returns no results"""
        url = reverse('user-search')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []


@pytest.mark.django_db
class TestUserInterests:
    """Test user interests functionality"""
    
    def test_create_user_interest(self, authenticated_client):
        """Test creating a new interest for authenticated user"""
        url = reverse('interest-list')
        data = {'name': 'Technology'}
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Technology'
        
        # Verify in database
        interest = UserInterest.objects.get(id=response.data['id'])
        assert interest.user == authenticated_client.user
        assert interest.name == 'Technology'
    
    def test_list_user_interests(self, authenticated_client):
        """Test listing interests for authenticated user"""
        # Create interests for the authenticated user
        baker.make(UserInterest, user=authenticated_client.user, name='Science')
        baker.make(UserInterest, user=authenticated_client.user, name='Art')
        
        # Create interest for another user (should not appear)
        other_user = baker.make(User)
        baker.make(UserInterest, user=other_user, name='Music')
        
        url = reverse('interest-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        interest_names = [i['name'] for i in response.data['results']]
        assert 'Science' in interest_names
        assert 'Art' in interest_names
        assert 'Music' not in interest_names
    
    def test_delete_user_interest(self, authenticated_client):
        """Test deleting an interest"""
        interest = baker.make(UserInterest, user=authenticated_client.user, name='Sports')
        
        url = reverse('interest-detail', kwargs={'pk': interest.id})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert UserInterest.objects.filter(id=interest.id).exists() is False
    
    def test_unauthenticated_cannot_access_interests(self, api_client):
        """Test unauthenticated users cannot access interests"""
        url = reverse('interest-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED