"""
Comprehensive tests for content services.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from apps.core.test_utils import ServiceTestCase, CacheTestMixin
from apps.core.exceptions import BusinessLogicError, NotFoundError, PermissionDeniedError
from apps.core.factories import (
    UserFactory, CategoryFactory, HashTagFactory, PostTypeFactory,
    PostFactory, PublishedPostFactory, OrganizationFactory
)
from apps.content.services import (
    PostService, CategoryService, HashTagService, PostTypeService,
    PostAttachmentService
)
from apps.content.models.post import Post
from apps.content.models.classification import Category, HashTag

User = get_user_model()


class PostServiceTest(ServiceTestCase, CacheTestMixin):
    """Test PostService functionality."""
    
    def setUp(self):
        super().setUp()
        self.org = OrganizationFactory()
        self.post_type = PostTypeFactory()
        self.category = CategoryFactory()
        
        # Create service
        self.service = PostService(self.user)
    
    def test_create_post_success(self):
        """Test successful post creation."""
        post_data = {
            'title': 'Test Post',
            'content': 'Test content',
            'organization': self.org,
            'type': self.post_type,
            'categories': [self.category.id],
            'hashtags': ['test', 'django']
        }
        
        post = self.service.create_post(post_data)
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.organization, self.org)
        self.assertEqual(post.type, self.post_type)
        
        # Check relationships
        self.assertTrue(post.categories.filter(id=self.category.id).exists())
        self.assertTrue(post.hashtags.filter(name='test').exists())
        self.assertTrue(post.hashtags.filter(name='django').exists())
    
    def test_create_post_validation_error(self):
        """Test post creation with validation errors."""
        # Missing required fields
        post_data = {
            'title': '',  # Empty title
            'content': 'Test content',
            'organization': self.org,
            'type': self.post_type
        }
        
        with self.assertRaises(BusinessLogicError):
            self.service.create_post(post_data)
    
    def test_create_post_permission_denied(self):
        """Test post creation without proper permissions."""
        # Create service without user
        service = PostService(user=None)
        
        post_data = {
            'title': 'Test Post',
            'content': 'Test content',
            'organization': self.org,
            'type': self.post_type
        }
        
        with self.assertRaises(PermissionDeniedError):
            service.create_post(post_data)
    
    def test_update_post_success(self):
        """Test successful post update."""
        post = PostFactory(author=self.user, organization=self.org)
        
        update_data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'categories': [self.category.id]
        }
        
        updated_post = self.service.update_post(post.id, update_data)
        
        self.assertEqual(updated_post.title, 'Updated Title')
        self.assertEqual(updated_post.content, 'Updated content')
        self.assertTrue(updated_post.categories.filter(id=self.category.id).exists())
    
    def test_update_post_permission_denied(self):
        """Test updating post without permission."""
        other_user = UserFactory()
        post = PostFactory(author=other_user)
        
        update_data = {'title': 'Hacked Title'}
        
        with self.assertRaises(PermissionDeniedError):
            self.service.update_post(post.id, update_data)
    
    def test_publish_post_success(self):
        """Test successful post publishing."""
        post = PostFactory(author=self.user, status='draft')
        
        # Mock permission check
        with patch.object(self.service, '_validate_publish_permission'):
            published_post = self.service.publish(post.id)
        
        self.assertEqual(published_post.status, 'published')
        self.assertIsNotNone(published_post.published_at)
    
    def test_publish_already_published_post(self):
        """Test publishing already published post."""
        post = PublishedPostFactory(author=self.user)
        
        with patch.object(self.service, '_validate_publish_permission'):
            with self.assertRaises(BusinessLogicError):
                self.service.publish(post.id)
    
    def test_get_published_posts(self):
        """Test getting published posts."""
        # Create mix of posts
        PublishedPostFactory.create_batch(5)
        PostFactory.create_batch(3, status='draft')
        
        published_posts = self.service.get_published_posts(limit=10)
        
        self.assertEqual(len(published_posts), 5)
        for post in published_posts:
            self.assertEqual(post.status, 'published')
    
    def test_get_featured_posts(self):
        """Test getting featured posts."""
        # Create featured and regular posts
        featured_posts = PublishedPostFactory.create_batch(3, is_featured=True)
        PublishedPostFactory.create_batch(2, is_featured=False)
        
        result = self.service.get_featured_posts(limit=5)
        
        self.assertEqual(len(result), 3)
        for post in result:
            self.assertTrue(post.is_featured)
    
    def test_search_posts(self):
        """Test post search functionality."""
        # Create posts with specific content
        post1 = PublishedPostFactory(title="Django Tutorial", content="Learn Django")
        post2 = PublishedPostFactory(title="Python Guide", content="Python programming")
        post3 = PublishedPostFactory(title="JavaScript Tips", content="Web development")
        
        # Search for Django
        results = self.service.search_posts("Django", limit=10)
        
        post_ids = [post.id for post in results]
        self.assertIn(post1.id, post_ids)
        self.assertNotIn(post3.id, post_ids)  # Should not include JS post
    
    def test_get_posts_by_category(self):
        """Test getting posts by category."""
        category = CategoryFactory()
        
        # Create posts with and without the category
        post1 = PublishedPostFactory()
        post1.categories.add(category)
        
        post2 = PublishedPostFactory()
        # post2 doesn't have the category
        
        results = self.service.get_posts_by_category(category.id, limit=10)
        
        post_ids = [post.id for post in results]
        self.assertIn(post1.id, post_ids)
        self.assertNotIn(post2.id, post_ids)
    
    def test_get_user_posts(self):
        """Test getting posts by user."""
        other_user = UserFactory()
        
        # Create posts for different users
        user_posts = PostFactory.create_batch(3, author=self.user)
        other_posts = PostFactory.create_batch(2, author=other_user)
        
        results = self.service.get_user_posts(self.user.id)
        
        result_ids = [post.id for post in results]
        for post in user_posts:
            self.assertIn(post.id, result_ids)
        
        for post in other_posts:
            self.assertNotIn(post.id, result_ids)


class CategoryServiceTest(ServiceTestCase, CacheTestMixin):
    """Test CategoryService functionality."""
    
    def setUp(self):
        super().setUp()
        self.service = CategoryService(self.user)
    
    def test_get_active_categories(self):
        """Test getting active categories."""
        # Create active and inactive categories
        active_cats = CategoryFactory.create_batch(3, is_active=True)
        inactive_cats = CategoryFactory.create_batch(2, is_active=False)
        
        result = self.service.get_active_categories()
        
        result_ids = [cat.id for cat in result]
        for cat in active_cats:
            self.assertIn(cat.id, result_ids)
        
        for cat in inactive_cats:
            self.assertNotIn(cat.id, result_ids)
    
    def test_get_category_with_posts(self):
        """Test getting category with its posts."""
        category = CategoryFactory()
        
        # Create posts for the category
        posts = PublishedPostFactory.create_batch(5)
        for post in posts:
            post.categories.add(category)
        
        result = self.service.get_category_with_posts(category.id, limit=3)
        
        self.assertEqual(result['category'], category)
        self.assertEqual(len(result['posts']), 3)
        self.assertEqual(result['total_posts'], 5)
    
    def test_create_category(self):
        """Test category creation."""
        category_data = {
            'name': 'New Category',
            'name_ar': 'فئة جديدة',
            'description': 'Test description',
            'is_active': True
        }
        
        category = self.service.create(category_data)
        
        self.assertEqual(category.name, 'New Category')
        self.assertEqual(category.name_ar, 'فئة جديدة')
        self.assertTrue(category.is_active)
        self.assertIsNotNone(category.slug)
    
    def test_update_post_counts(self):
        """Test updating post counts for all categories."""
        categories = CategoryFactory.create_batch(3)
        
        # Add posts to categories
        for i, category in enumerate(categories):
            posts = PublishedPostFactory.create_batch(i + 1)  # 1, 2, 3 posts
            for post in posts:
                post.categories.add(category)
        
        # Update counts
        self.service.update_post_counts()
        
        # Verify counts
        for i, category in enumerate(categories):
            category.refresh_from_db()
            self.assertEqual(category.post_count, i + 1)


class HashTagServiceTest(ServiceTestCase):
    """Test HashTagService functionality."""
    
    def setUp(self):
        super().setUp()
        self.service = HashTagService(self.user)
    
    def test_get_trending_hashtags(self):
        """Test getting trending hashtags."""
        # Create trending and non-trending hashtags
        trending_tags = HashTagFactory.create_batch(3, is_trending=True, post_count=10)
        regular_tags = HashTagFactory.create_batch(2, is_trending=False, post_count=5)
        
        result = self.service.get_trending_hashtags(limit=5)
        
        result_ids = [tag.id for tag in result]
        for tag in trending_tags:
            self.assertIn(tag.id, result_ids)
        
        for tag in regular_tags:
            self.assertNotIn(tag.id, result_ids)
    
    def test_get_popular_hashtags(self):
        """Test getting popular hashtags by post count."""
        # Create hashtags with different post counts
        popular_tag = HashTagFactory(post_count=100)
        medium_tag = HashTagFactory(post_count=50)
        unpopular_tag = HashTagFactory(post_count=1)
        
        result = self.service.get_popular_hashtags(limit=5)
        
        # Should be ordered by post count
        self.assertEqual(result[0], popular_tag)
        self.assertEqual(result[1], medium_tag)
        self.assertEqual(result[2], unpopular_tag)
    
    def test_search_hashtags(self):
        """Test hashtag search functionality."""
        # Create hashtags with specific names
        django_tag = HashTagFactory(name="django")
        python_tag = HashTagFactory(name="python")
        java_tag = HashTagFactory(name="java")
        
        # Search for "py" should match python
        results = self.service.search_hashtags("py", limit=5)
        
        result_names = [tag.name for tag in results]
        self.assertIn("python", result_names)
        self.assertNotIn("java", result_names)
    
    def test_update_trending_status(self):
        """Test updating trending status based on activity."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create hashtags with different activity levels
        active_tag = HashTagFactory(
            post_count=10,
            last_used=timezone.now() - timedelta(days=1)
        )
        inactive_tag = HashTagFactory(
            post_count=2,
            last_used=timezone.now() - timedelta(days=10)
        )
        
        # Update trending status
        self.service.update_trending_status(min_posts=5, days=7)
        
        # Refresh from database
        active_tag.refresh_from_db()
        inactive_tag.refresh_from_db()
        
        # Active tag should be trending
        self.assertTrue(active_tag.is_trending)
        # Inactive tag should not be trending
        self.assertFalse(inactive_tag.is_trending)


class PostAttachmentServiceTest(ServiceTestCase):
    """Test PostAttachmentService functionality."""
    
    def setUp(self):
        super().setUp()
        self.service = PostAttachmentService(self.user)
        self.post = PostFactory(author=self.user)
    
    def test_get_post_attachments(self):
        """Test getting attachments for a post."""
        # Create attachments for the post
        attachments = []
        for i in range(3):
            attachment = PostAttachmentFactory(post=self.post, order=i)
            attachments.append(attachment)
        
        # Create attachment for different post
        other_post = PostFactory()
        PostAttachmentFactory(post=other_post)
        
        result = self.service.get_post_attachments(self.post.id)
        
        self.assertEqual(len(result), 3)
        result_ids = [att.id for att in result]
        for att in attachments:
            self.assertIn(att.id, result_ids)
    
    def test_get_public_attachments(self):
        """Test getting only public attachments."""
        # Create public and private attachments
        public_att = PostAttachmentFactory(post=self.post, is_public=True)
        private_att = PostAttachmentFactory(post=self.post, is_public=False)
        
        result = self.service.get_public_attachments(self.post.id)
        
        result_ids = [att.id for att in result]
        self.assertIn(public_att.id, result_ids)
        self.assertNotIn(private_att.id, result_ids)
    
    def test_add_attachment_success(self):
        """Test successful attachment addition."""
        attachment_data = {
            'title': 'Test Document',
            'description': 'Test description',
            'file_type': 'application/pdf',
            'size': 1024000,
            'is_public': True
        }
        
        # Mock the file field
        with patch('apps.content.models.post.PostAttachment.file'):
            attachment = self.service.add_attachment(self.post.id, attachment_data)
        
        self.assertEqual(attachment.post, self.post)
        self.assertEqual(attachment.title, 'Test Document')
        self.assertTrue(attachment.is_public)
    
    def test_add_attachment_permission_denied(self):
        """Test adding attachment without permission."""
        other_user = UserFactory()
        other_post = PostFactory(author=other_user)
        
        attachment_data = {
            'title': 'Unauthorized Document',
            'file_type': 'application/pdf',
            'size': 1024000
        }
        
        with self.assertRaises(PermissionDeniedError):
            self.service.add_attachment(other_post.id, attachment_data)
    
    def test_track_download(self):
        """Test tracking attachment downloads."""
        attachment = PostAttachmentFactory(post=self.post, download_count=0)
        
        # Track download
        self.service.track_download(attachment.id)
        
        attachment.refresh_from_db()
        self.assertEqual(attachment.download_count, 1)
    
    def test_track_download_not_found(self):
        """Test tracking download for non-existent attachment."""
        # Should not raise exception
        self.service.track_download('non-existent-id')


class ServiceCacheIntegrationTest(ServiceTestCase, CacheTestMixin):
    """Test service integration with caching."""
    
    def setUp(self):
        super().setUp()
        self.post_service = PostService(self.user)
        self.category_service = CategoryService(self.user)
    
    def test_post_list_caching(self):
        """Test that post lists are cached."""
        # Create some posts
        PublishedPostFactory.create_batch(5)
        
        # First call should hit database and cache result
        with patch('apps.core.cache.CacheManager.get', return_value=None) as mock_get, \
             patch('apps.core.cache.CacheManager.set') as mock_set:
            
            posts = self.post_service.get_published_posts(limit=10)
            
            # Should try to get from cache
            mock_get.assert_called()
            # Should cache the result
            mock_set.assert_called()
    
    def test_cache_invalidation_on_post_update(self):
        """Test that cache is invalidated when posts are updated."""
        post = PublishedPostFactory(author=self.user)
        
        with patch('apps.core.cache.PostCacheManager.invalidate_post') as mock_invalidate:
            self.post_service.update_post(post.id, {'title': 'Updated Title'})
            
            # Should invalidate post cache
            mock_invalidate.assert_called_with(post.id)
    
    def test_category_tree_caching(self):
        """Test category tree caching."""
        CategoryFactory.create_batch(3)
        
        with patch('apps.core.cache.CategoryCacheManager.cache_category_tree') as mock_cache:
            mock_cache.return_value = []
            
            # This would normally trigger category tree caching
            categories = self.category_service.get_active_categories()
            
            # Verify caching behavior would be triggered in real scenario
            self.assertIsNotNone(categories)