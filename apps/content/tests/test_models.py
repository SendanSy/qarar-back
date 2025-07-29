"""
Comprehensive tests for content models.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model

from apps.core.test_utils import BaseTestCase, DatabaseTestMixin
from apps.core.factories import (
    UserFactory, CategoryFactory, SubCategoryFactory, HashTagFactory,
    PostTypeFactory, PostFactory, PublishedPostFactory, PostAttachmentFactory,
    BookmarkFactory, BookmarkCollectionFactory, OrganizationFactory
)
from apps.content.models.classification import Category, SubCategory, HashTag
from apps.content.models.post import Post, PostType, PostAttachment
from apps.content.models.bookmark import Bookmark, BookmarkCollection

User = get_user_model()


class CategoryModelTest(BaseTestCase, DatabaseTestMixin):
    """Test Category model functionality."""
    
    def test_category_creation(self):
        """Test basic category creation."""
        category = CategoryFactory(
            name="Government Decisions",
            name_ar="قرارات حكومية"
        )
        
        self.assertEqual(category.name, "Government Decisions")
        self.assertEqual(category.name_ar, "قرارات حكومية")
        self.assertTrue(category.is_active)
        self.assertFalse(category.is_deleted)
        self.assertIsNotNone(category.slug)
    
    def test_category_slug_generation(self):
        """Test automatic slug generation."""
        category = Category.objects.create(
            name="Test Category with Spaces",
            name_ar="فئة اختبار"
        )
        
        # Slug should be generated automatically
        self.assertIsNotNone(category.slug)
        self.assertIn("test-category", category.slug.lower())
    
    def test_category_unique_constraints(self):
        """Test unique constraints on category fields."""
        category1 = CategoryFactory(name="Unique Name")
        
        # Should not be able to create another category with same name
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CategoryFactory(name="Unique Name")
    
    def test_category_soft_delete(self):
        """Test soft delete functionality."""
        category = CategoryFactory()
        category_id = category.id
        
        # Soft delete
        category.delete()
        
        # Should be marked as deleted
        category.refresh_from_db()
        self.assertTrue(category.is_deleted)
        self.assertIsNotNone(category.deleted_at)
        
        # Should not appear in normal queries
        self.assertFalse(
            Category.objects.filter(id=category_id).exists()
        )
        
        # Should appear in with_deleted queries
        self.assertTrue(
            Category.objects.with_deleted().filter(id=category_id).exists()
        )
    
    def test_category_post_count_update(self):
        """Test post count update functionality."""
        category = CategoryFactory()
        
        # Initially no posts
        self.assertEqual(category.post_count, 0)
        
        # Create published posts
        for _ in range(3):
            post = PublishedPostFactory()
            post.categories.add(category)
        
        # Update count
        category.update_post_count()
        
        self.assertEqual(category.post_count, 3)
    
    def test_category_validation(self):
        """Test category field validation."""
        # Test empty names
        category = Category(name="", name_ar="")
        
        with self.assertRaises(ValidationError):
            category.full_clean()


class HashTagModelTest(BaseTestCase):
    """Test HashTag model functionality."""
    
    def test_hashtag_creation(self):
        """Test basic hashtag creation."""
        hashtag = HashTagFactory(name="django")
        
        self.assertEqual(hashtag.name, "django")
        self.assertIsNotNone(hashtag.slug)
        self.assertEqual(hashtag.post_count, 0)
        self.assertFalse(hashtag.is_trending)
    
    def test_hashtag_extraction(self):
        """Test hashtag extraction from content."""
        content = "This is a test with #django and #python hashtags"
        hashtags = HashTag.extract_from_content(content)
        
        self.assertIn("django", hashtags)
        self.assertIn("python", hashtags)
        self.assertEqual(len(hashtags), 2)
    
    def test_hashtag_extraction_arabic(self):
        """Test hashtag extraction with Arabic content."""
        content = "هذا نص تجريبي مع #تطوير و #برمجة"
        hashtags = HashTag.extract_from_content(content)
        
        self.assertIn("تطوير", hashtags)
        self.assertIn("برمجة", hashtags)
    
    def test_hashtag_validation(self):
        """Test hashtag name validation."""
        # Valid hashtag
        hashtag = HashTag(name="valid_tag")
        hashtag.full_clean()  # Should not raise
        
        # Invalid hashtag with special characters
        hashtag = HashTag(name="invalid-tag!")
        with self.assertRaises(ValidationError):
            hashtag.full_clean()
    
    def test_hashtag_trending_methods(self):
        """Test trending hashtag methods."""
        hashtag = HashTagFactory()
        
        # Mark as trending
        hashtag.mark_trending()
        self.assertTrue(hashtag.is_trending)
        
        # Unmark trending
        hashtag.unmark_trending()
        self.assertFalse(hashtag.is_trending)
    
    def test_hashtag_name_cleaning(self):
        """Test hashtag name cleaning on save."""
        hashtag = HashTag.objects.create(name="#django")
        
        # The # should be removed
        self.assertEqual(hashtag.name, "django")


class PostModelTest(BaseTestCase):
    """Test Post model functionality."""
    
    def setUp(self):
        super().setUp()
        self.post_type = PostTypeFactory()
    
    def test_post_creation(self):
        """Test basic post creation."""
        post = PostFactory(
            title="Test Post",
            content="Test content",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        
        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.status, 'draft')  # Default status
        self.assertIsNotNone(post.slug)
    
    def test_post_slug_generation(self):
        """Test automatic slug generation."""
        post = Post.objects.create(
            title="Test Post with Long Title",
            content="Content",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        
        self.assertIsNotNone(post.slug)
        self.assertIn("test-post", post.slug.lower())
    
    def test_post_slug_uniqueness(self):
        """Test slug uniqueness constraint."""
        # Create first post
        post1 = PostFactory(title="Same Title")
        
        # Create second post with same title
        post2 = PostFactory(title="Same Title")
        
        # Slugs should be different
        self.assertNotEqual(post1.slug, post2.slug)
    
    def test_post_publishing(self):
        """Test post publishing functionality."""
        post = PostFactory(status='draft')
        
        # Publish the post
        post.publish()
        
        self.assertEqual(post.status, 'published')
        self.assertIsNotNone(post.published_at)
    
    def test_post_reading_time_calculation(self):
        """Test reading time calculation."""
        # Short content
        post = PostFactory(content="Short content")
        self.assertEqual(post.reading_time, 1)  # Minimum 1 minute
        
        # Long content (200+ words)
        long_content = " ".join(["word"] * 250)
        post = PostFactory(content=long_content)
        self.assertGreaterEqual(post.reading_time, 1)
    
    def test_post_view_tracking(self):
        """Test view count tracking."""
        post = PostFactory()
        initial_count = post.view_count
        
        # Increment view count
        post.increment_view_count()
        
        self.assertEqual(post.view_count, initial_count + 1)
    
    def test_post_bilingual_methods(self):
        """Test bilingual content methods."""
        post = PostFactory(
            title="English Title",
            title_ar="عنوان عربي",
            content="English content",
            content_ar="محتوى عربي"
        )
        
        # Test English
        self.assertEqual(post.get_display_title('en'), "English Title")
        self.assertEqual(post.get_display_content('en'), "English content")
        
        # Test Arabic
        self.assertEqual(post.get_display_title('ar'), "عنوان عربي")
        self.assertEqual(post.get_display_content('ar'), "محتوى عربي")
    
    def test_post_validation(self):
        """Test post field validation."""
        # Test empty title and title_ar
        post = Post(
            title="", title_ar="",
            content="Content",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        
        with self.assertRaises(ValidationError):
            post.full_clean()
        
        # Test empty content and content_ar
        post = Post(
            title="Title",
            content="", content_ar="",
            author=self.user,
            organization=self.organization,
            type=self.post_type
        )
        
        with self.assertRaises(ValidationError):
            post.full_clean()
    
    def test_post_hashtag_extraction(self):
        """Test automatic hashtag extraction."""
        post = PostFactory(
            content="This post is about #django and #python development",
            status='published'
        )
        
        # Save should trigger hashtag extraction
        post.save()
        
        # Check hashtags were created and associated
        hashtag_names = [ht.name for ht in post.hashtags.all()]
        self.assertIn("django", hashtag_names)
        self.assertIn("python", hashtag_names)


class PostAttachmentModelTest(BaseTestCase):
    """Test PostAttachment model functionality."""
    
    def test_attachment_creation(self):
        """Test basic attachment creation."""
        post = PostFactory()
        attachment = PostAttachmentFactory(
            post=post,
            title="Test Document",
            file_type="application/pdf",
            size=1024000
        )
        
        self.assertEqual(attachment.post, post)
        self.assertEqual(attachment.title, "Test Document")
        self.assertTrue(attachment.is_public)
    
    def test_attachment_type_detection(self):
        """Test file type detection methods."""
        # PDF attachment
        pdf_attachment = PostAttachmentFactory(file_type="application/pdf")
        self.assertTrue(pdf_attachment.is_document)
        self.assertFalse(pdf_attachment.is_image)
        
        # Image attachment
        img_attachment = PostAttachmentFactory(file_type="image/jpeg")
        self.assertTrue(img_attachment.is_image)
        self.assertFalse(img_attachment.is_document)
    
    def test_attachment_size_formatting(self):
        """Test file size formatting."""
        # Test different sizes
        small_file = PostAttachmentFactory(size=512)  # 512 B
        self.assertEqual(small_file.formatted_size, "512.0 B")
        
        medium_file = PostAttachmentFactory(size=1024 * 500)  # 500 KB
        self.assertEqual(medium_file.formatted_size, "500.0 KB")
        
        large_file = PostAttachmentFactory(size=1024 * 1024 * 5)  # 5 MB
        self.assertEqual(large_file.formatted_size, "5.0 MB")
    
    def test_attachment_download_tracking(self):
        """Test download count tracking."""
        attachment = PostAttachmentFactory()
        initial_count = attachment.download_count
        
        # Track download
        attachment.increment_download_count()
        
        self.assertEqual(attachment.download_count, initial_count + 1)


class BookmarkModelTest(BaseTestCase):
    """Test Bookmark model functionality."""
    
    def test_bookmark_creation(self):
        """Test basic bookmark creation."""
        post = PublishedPostFactory()
        bookmark = BookmarkFactory(
            user=self.user,
            post=post,
            notes="Interesting article"
        )
        
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(bookmark.post, post)
        self.assertTrue(bookmark.is_private)
    
    def test_bookmark_unique_constraint(self):
        """Test unique constraint on user-post combination."""
        post = PublishedPostFactory()
        
        # Create first bookmark
        BookmarkFactory(user=self.user, post=post)
        
        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BookmarkFactory(user=self.user, post=post)
    
    def test_bookmark_tag_methods(self):
        """Test bookmark tag handling methods."""
        bookmark = BookmarkFactory(tags="tag1, tag2, tag3")
        
        # Test get_tag_list
        tag_list = bookmark.get_tag_list()
        self.assertEqual(tag_list, ["tag1", "tag2", "tag3"])
        
        # Test set_tag_list
        bookmark.set_tag_list(["new1", "new2"])
        self.assertEqual(bookmark.tags, "new1, new2")
    
    def test_bookmark_validation(self):
        """Test bookmark validation rules."""
        # Try to bookmark unpublished post
        draft_post = PostFactory(status='draft')
        bookmark = Bookmark(
            user=self.user,
            post=draft_post
        )
        
        with self.assertRaises(ValidationError):
            bookmark.full_clean()


class BookmarkCollectionModelTest(BaseTestCase):
    """Test BookmarkCollection model functionality."""
    
    def test_collection_creation(self):
        """Test basic collection creation."""
        collection = BookmarkCollectionFactory(
            user=self.user,
            name="My Favorites",
            color="#ff0000"
        )
        
        self.assertEqual(collection.user, self.user)
        self.assertEqual(collection.name, "My Favorites")
        self.assertEqual(collection.color, "#ff0000")
    
    def test_collection_unique_constraint(self):
        """Test unique constraint on user-name combination."""
        # Create first collection
        BookmarkCollectionFactory(user=self.user, name="Favorites")
        
        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BookmarkCollectionFactory(user=self.user, name="Favorites")
    
    def test_collection_bookmark_count(self):
        """Test bookmark count property."""
        collection = BookmarkCollectionFactory(user=self.user)
        
        # Initially empty
        self.assertEqual(collection.bookmark_count, 0)
        
        # Add bookmarks
        bookmarks = BookmarkFactory.create_batch(3, user=self.user)
        for bookmark in bookmarks:
            collection.bookmarks.add(bookmark)
        
        self.assertEqual(collection.bookmark_count, 3)
    
    def test_collection_color_validation(self):
        """Test color field validation."""
        # Valid color
        collection = BookmarkCollection(
            user=self.user,
            name="Test",
            color="#ff0000"
        )
        collection.full_clean()  # Should not raise
        
        # Invalid color format
        collection = BookmarkCollection(
            user=self.user,
            name="Test",
            color="red"
        )
        
        with self.assertRaises(ValidationError):
            collection.full_clean()


class ModelManagerTest(BaseTestCase, DatabaseTestMixin):
    """Test custom model managers."""
    
    def test_category_manager_optimizations(self):
        """Test CategoryManager query optimizations."""
        # Create test data
        category = CategoryFactory()
        subcategories = SubCategoryFactory.create_batch(3, category=category)
        
        # Create posts for the category
        for _ in range(5):
            post = PublishedPostFactory()
            post.categories.add(category)
        
        # Test optimized queryset
        with self.assertMaxQueryCount(3):  # Should be efficient
            categories = list(Category.objects.with_post_counts())
            for cat in categories:
                # Access annotated fields
                _ = cat.published_post_count
                _ = cat.total_posts
    
    def test_post_manager_optimizations(self):
        """Test PostManager query optimizations."""
        # Create test data
        posts = PublishedPostFactory.create_batch(10)
        
        # Test optimized list view
        with self.assertMaxQueryCount(5):  # Should be efficient
            post_list = list(Post.objects.for_api_list()[:5])
            for post in post_list:
                # Access related fields
                _ = post.author.username
                _ = post.type.name
                _ = post.organization.name
    
    def test_soft_delete_manager(self):
        """Test SoftDeleteManager functionality."""
        # Create and delete some categories
        active_category = CategoryFactory()
        deleted_category = CategoryFactory()
        deleted_category.delete()
        
        # Normal manager should only return active
        active_count = Category.objects.count()
        self.assertEqual(active_count, 1)
        
        # with_deleted should return all
        total_count = Category.objects.with_deleted().count()
        self.assertEqual(total_count, 2)
        
        # deleted_only should return only deleted
        deleted_count = Category.objects.deleted_only().count()
        self.assertEqual(deleted_count, 1)