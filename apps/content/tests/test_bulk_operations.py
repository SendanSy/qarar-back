"""
Tests for bulk operations service.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.factories import UserFactory
from apps.content.models.post import Post, PostType
from apps.content.models.classification import Category
from apps.content.models.bookmark import Bookmark
from apps.content.bulk_operations import BulkOperationService, BulkImportService
from apps.producers.models import Organization

User = get_user_model()


class BulkOperationServiceTest(TestCase):
    """Test bulk operations service."""
    
    def setUp(self):
        self.user = UserFactory()
        self.user.is_superuser = True  # Grant permission to create posts
        self.user.save()
        self.service = BulkOperationService(self.user)
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
    
    def test_bulk_create_posts(self):
        """Test bulk creating posts."""
        posts_data = [
            {
                'title': 'Post 1',
                'content': 'Content 1',
                'organization': self.organization,
                'type': self.post_type,
            },
            {
                'title': 'Post 2',
                'content': 'Content 2',
                'organization': self.organization,
                'type': self.post_type,
            }
        ]
        
        created_posts = self.service.bulk_create_posts(posts_data)
        
        self.assertEqual(len(created_posts), 2)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(created_posts[0].title, 'Post 1')
        self.assertEqual(created_posts[1].title, 'Post 2')
    
    def test_bulk_publish_posts(self):
        """Test bulk publishing posts."""
        # Create draft posts
        post1 = Post.objects.create(
            title="Draft Post 1",
            content="Content 1",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='draft'
        )
        post2 = Post.objects.create(
            title="Draft Post 2",
            content="Content 2",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='draft'
        )
        
        post_ids = [str(post1.id), str(post2.id)]
        published_posts = self.service.bulk_publish_posts(post_ids)
        
        self.assertEqual(len(published_posts), 2)
        
        # Refresh from database
        post1.refresh_from_db()
        post2.refresh_from_db()
        
        self.assertEqual(post1.status, 'published')
        self.assertEqual(post2.status, 'published')
        self.assertIsNotNone(post1.published_at)
        self.assertIsNotNone(post2.published_at)
    
    def test_bulk_delete_posts(self):
        """Test bulk deleting posts (soft delete)."""
        post1 = Post.objects.create(
            title="Post 1",
            content="Content 1",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        post2 = Post.objects.create(
            title="Post 2",
            content="Content 2",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        
        post_ids = [str(post1.id), str(post2.id)]
        deleted_count = self.service.bulk_delete_posts(post_ids)
        
        self.assertEqual(deleted_count, 2)
        
        # Check soft delete
        post1.refresh_from_db()
        post2.refresh_from_db()
        
        self.assertTrue(post1.is_deleted)
        self.assertTrue(post2.is_deleted)
    
    def test_bulk_categorize_posts(self):
        """Test bulk adding categories to posts."""
        post1 = Post.objects.create(
            title="Post 1",
            content="Content 1",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        post2 = Post.objects.create(
            title="Post 2",
            content="Content 2",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        
        post_ids = [str(post1.id), str(post2.id)]
        category_ids = [str(self.category.id)]
        
        affected_count = self.service.bulk_categorize_posts(
            post_ids, category_ids, action='add'
        )
        
        self.assertEqual(affected_count, 2)
        self.assertTrue(post1.categories.filter(id=self.category.id).exists())
        self.assertTrue(post2.categories.filter(id=self.category.id).exists())
    
    def test_bulk_create_bookmarks(self):
        """Test bulk creating bookmarks."""
        post1 = Post.objects.create(
            title="Post 1",
            content="Content 1",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
        post2 = Post.objects.create(
            title="Post 2",
            content="Content 2",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
        
        bookmark_data = [
            {'post_id': str(post1.id), 'notes': 'Important'},
            {'post_id': str(post2.id), 'notes': 'To review'}
        ]
        
        created_bookmarks = self.service.bulk_create_bookmarks(bookmark_data)
        
        self.assertEqual(len(created_bookmarks), 2)
        self.assertEqual(Bookmark.objects.count(), 2)
    
    def test_bulk_export_posts_json(self):
        """Test bulk exporting posts as JSON."""
        post1 = Post.objects.create(
            title="Post 1",
            content="Content 1",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
        post2 = Post.objects.create(
            title="Post 2",
            content="Content 2",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
        
        post_ids = [str(post1.id), str(post2.id)]
        export_data = self.service.bulk_export_posts(post_ids, format='json')
        
        self.assertEqual(export_data['format'], 'json')
        self.assertEqual(export_data['count'], 2)
        self.assertIn('data', export_data)
        self.assertEqual(len(export_data['data']), 2)
    
    def test_bulk_export_posts_csv(self):
        """Test bulk exporting posts as CSV."""
        post1 = Post.objects.create(
            title="Post 1",
            content="Content 1",
            author=self.user,
            organization=self.organization,
            type=self.post_type,
            status='published'
        )
        
        post_ids = [str(post1.id)]
        export_data = self.service.bulk_export_posts(post_ids, format='csv')
        
        self.assertEqual(export_data['format'], 'csv')
        self.assertEqual(export_data['count'], 1)
        self.assertIn('data', export_data)
        self.assertIn('Post 1', export_data['data'])
    
    def test_bulk_operations_limits(self):
        """Test bulk operation limits."""
        # Test creation limit
        posts_data = [
            {
                'title': f'Post {i}',
                'content': f'Content {i}',
                'organization': self.organization.id,
                'type': self.post_type.id,
            }
            for i in range(101)  # More than limit
        ]
        
        with self.assertRaises(Exception):
            self.service.bulk_create_posts(posts_data)


class BulkImportServiceTest(TestCase):
    """Test bulk import service."""
    
    def setUp(self):
        self.user = UserFactory()
        self.user.is_superuser = True  # Grant permission to create posts
        self.user.save()
        self.service = BulkImportService(self.user)
        self.organization = Organization.objects.create(
            name="Test Org",
            name_ar="منظمة اختبار"
        )
        self.post_type = PostType.objects.create(
            name="Decision",
            name_ar="قرار"
        )
    
    def test_import_posts_from_json(self):
        """Test importing posts from JSON."""
        json_data = {
            'data': [
                {
                    'title': 'Imported Post 1',
                    'content': 'Imported content 1',
                    'organization': str(self.organization.id),
                    'type': str(self.post_type.id),
                },
                {
                    'title': 'Imported Post 2',
                    'content': 'Imported content 2',
                    'organization': str(self.organization.id),
                    'type': str(self.post_type.id),
                }
            ]
        }
        
        result = self.service.import_posts_from_json(json_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported_count'], 2)
        self.assertEqual(Post.objects.count(), 2)
    
    def test_import_posts_from_csv(self):
        """Test importing posts from CSV."""
        csv_data = '''Title,Content,Organization ID,Type ID
Test Post 1,Test content 1,{org_id},{type_id}
Test Post 2,Test content 2,{org_id},{type_id}'''.format(
            org_id=self.organization.id,
            type_id=self.post_type.id
        )
        
        result = self.service.import_posts_from_csv(csv_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported_count'], 2)
        self.assertEqual(Post.objects.count(), 2)
    
    def test_import_invalid_json(self):
        """Test importing with invalid JSON structure."""
        json_data = {'invalid': 'structure'}
        
        with self.assertRaises(Exception):
            self.service.import_posts_from_json(json_data)