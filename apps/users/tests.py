import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserInterest, UserFollowing

User = get_user_model()


class UserModelTest(TestCase):
    """Test case for User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
    def test_create_user(self):
        """Test creating a user"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertTrue(self.user.check_password('testpass123'))
        
    def test_user_interest(self):
        """Test creating user interests"""
        interest = UserInterest.objects.create(user=self.user, name='Technology')
        self.assertEqual(interest.name, 'Technology')
        self.assertEqual(interest.user, self.user)
        
    def test_user_following(self):
        """Test user following relationship"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpass123'
        )
        following = UserFollowing.objects.create(user=self.user, following_user=other_user)
        self.assertEqual(following.user, self.user)
        self.assertEqual(following.following_user, other_user)
        

class UserAPITest(APITestCase):
    """Test case for User API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='User'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
    def get_tokens_for_user(self, user):
        """Get JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuserpass123',
            'password2': 'newuserpass123',
            'first_name': 'New',
            'last_name': 'User',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)  # Total users after registration
        
    def test_user_login(self):
        """Test user login endpoint"""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'testpass123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_user_detail(self):
        """Test retrieving user details"""
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        # Anonymous access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Authenticated access
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_tokens_for_user(self.user)["access"]}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_user_update(self):
        """Test updating user profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_tokens_for_user(self.user)["access"]}')
        url = reverse('user-update-me')
        data = {
            'bio': 'My new bio',
            'location': 'New York',
            'website': 'https://example.com',
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'My new bio')
        self.assertEqual(self.user.location, 'New York')
        
    def test_user_follow_unfollow(self):
        """Test following and unfollowing users"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_tokens_for_user(self.user)["access"]}')
        
        # Follow
        url = reverse('user-follow', kwargs={'pk': self.other_user.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(UserFollowing.objects.filter(user=self.user, following_user=self.other_user).exists())
        
        # Unfollow
        url = reverse('user-unfollow', kwargs={'pk': self.other_user.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(UserFollowing.objects.filter(user=self.user, following_user=self.other_user).exists())
        
    def test_change_password(self):
        """Test changing user password"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_tokens_for_user(self.user)["access"]}')
        url = reverse('user-change-password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newtestpass123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newtestpass123'))
        
    def test_user_interests(self):
        """Test user interests endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_tokens_for_user(self.user)["access"]}')
        
        # Add interest
        url = reverse('interest-list')
        data = {'name': 'Technology'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Store the ID of the created interest
        interest_id = response.data.get('id')
        self.assertIsNotNone(interest_id, "Interest ID is missing in response")
        
        # Get interests
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Delete the specific interest we created
        url = reverse('interest-detail', kwargs={'pk': interest_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserInterest.objects.filter(id=interest_id).exists())
        
    def test_user_me_endpoint(self):
        """Test current user endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_tokens_for_user(self.user)["access"]}')
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)
