"""
Tests for content views.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.core.factories import UserFactory
from apps.content.models.post import Post, PostType
from apps.content.models.classification import Category, HashTag
from apps.content.models.bookmark import Bookmark
from apps.producers.models import Organization

User = get_user_model()


class PostViewSetTest(APITestCase):
    """Test PostViewSet functionality."""
    
    def setUp(self):
        self.user = UserFactory()
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="Test Org",
            name_ar="منظمة اختبار"
        )
        self.post_type = PostType.objects.create(
            name="Decision",
            name_ar="قرار"
        )
        self.category = Category.objects.create(
            name="Test Category",
            name_ar="فئة اختبار"
        )
        
    def test_list_posts_anonymous(self):
        """Test listing posts as anonymous user."""
        # Create published post
        Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
        
        # Create draft post (should not be visible)
        Post.objects.create(
            title="Draft Post",
            content="Draft content",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='draft'
        )
        
        url = reverse('post-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Test Post")
    
    def test_create_post_authenticated(self):
        """Test creating a post as authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'New Post',
            'content': 'New content',
            'organization': self.organization.id,
            'type_id': self.post_type.id,
            'status': 'draft'
        }
        
        url = reverse('post-list')
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().author, self.user)
    
    def test_bookmark_post(self):
        """Test bookmarking a post."""
        self.client.force_authenticate(user=self.user)
        
        post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
        
        url = reverse('post-bookmark', kwargs={'slug': post.slug})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Bookmark.objects.filter(user=self.user, post=post).exists())
    
    def test_featured_posts(self):
        """Test fetching featured posts."""
        post = Post.objects.create(
            title="Featured Post",
            content="Featured content",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published',
            is_featured=True
        )
        
        url = reverse('post-featured')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Featured Post")


class CategoryViewSetTest(APITestCase):
    """Test CategoryViewSet functionality."""
    
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category",
            name_ar="فئة اختبار"
        )
    
    def test_list_categories(self):
        """Test listing categories."""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Test Category")
    
    def test_category_posts(self):
        """Test getting posts for a category."""
        user = UserFactory()
        organization = Organization.objects.create(name="Test Org")
        post_type = PostType.objects.create(name="Decision")
        
        post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=user,
            organization=organization,
            type=post_type,
            status='published'
        )
        post.categories.add(self.category)
        
        url = reverse('category-posts', kwargs={'slug': self.category.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['posts']), 1)
        self.assertEqual(response.data['posts'][0]['title'], "Test Post")


class SearchViewSetTest(APITestCase):
    """Test SearchViewSet functionality."""
    
    def setUp(self):
        self.user = UserFactory()
        self.organization = Organization.objects.create(name="Test Org")
        self.post_type = PostType.objects.create(name="Decision")
        
        self.post = Post.objects.create(
            title="Searchable Post",
            content="This is searchable content",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
    
    def test_search_posts(self):
        """Test searching for posts."""
        url = reverse('search-list')
        response = self.client.get(url, {'q': 'searchable'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_results'], 1)
        self.assertEqual(response.data['results'][0]['title'], "Searchable Post")
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        url = reverse('search-list')
        response = self.client.get(url, {'q': ''})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_autocomplete(self):
        """Test search autocomplete."""
        url = reverse('search-autocomplete')
        response = self.client.get(url, {'q': 'search'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Searchable Post", response.data)


class HealthCheckViewSetTest(APITestCase):
    """Test HealthCheckViewSet functionality."""
    
    def test_basic_health_check(self):
        """Test basic health check."""
        url = reverse('health-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
    
    def test_detailed_health_check(self):
        """Test detailed health check."""
        url = reverse('health-detailed')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('components', response.data)
        self.assertIn('database', response.data['components'])


class BookmarkViewSetTest(APITestCase):
    """Test BookmarkViewSet functionality."""
    
    def setUp(self):
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.organization = Organization.objects.create(name="Test Org")
        self.post_type = PostType.objects.create(name="Decision")
        
        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
    
    def test_create_bookmark(self):
        """Test creating a bookmark."""
        data = {
            'post_id': self.post.id,
            'notes': 'Important post'
        }
        
        url = reverse('bookmark-list')
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bookmark.objects.count(), 1)
    
    def test_list_bookmarks(self):
        """Test listing user bookmarks."""
        Bookmark.objects.create(
            user=self.user,
            post=self.post,
            notes="Test bookmark"
        )
        
        url = reverse('bookmark-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_bookmark_posts(self):
        """Test getting bookmarked posts."""
        Bookmark.objects.create(
            user=self.user,
            post=self.post,
            notes="Test bookmark"
        )
        
        url = reverse('bookmark-posts')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Test Post")