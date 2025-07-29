import tempfile
from PIL import Image as PILImage
from io import BytesIO
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType

from .models import (
    Category,
    Bookmark,
    Post,
    PostType,
    PostAttachment
)
from apps.producers.models import Organization
from apps.geographics.models import Country

User = get_user_model()


def create_temp_image():
    """Helper function to create a temporary image for testing"""
    image = PILImage.new('RGB', (100, 100), color='red')
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return SimpleUploadedFile(
        "test_image.jpg", 
        image_io.getvalue(),
        content_type="image/jpeg"
    )


class CategoryTest(TestCase):
    """Test case for Category model"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test description'
        )
    
    def test_category_creation(self):
        """Test category creation"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertEqual(str(self.category), 'Test Category')


class PostTest(TestCase):
    """Test case for Post model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            name_ar='فئة تجريبية',
            slug='test-category'
        )
        self.country = Country.objects.create(
            name='Test Country',
            code='TC'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TO',
            country=self.country
        )
        self.post_type = PostType.objects.create(
            name='Test Type',
            name_ar='نوع تجريبي'
        )
        self.post = Post.objects.create(
            title='Test Post',
            author=self.user,
            content='Test post content',
            status='published',
            type=self.post_type,
            organization=self.organization
        )
        self.post.categories.add(self.category)
    
    def test_post_creation(self):
        """Test post creation"""
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.content, 'Test post content')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.status, 'published')
        self.assertEqual(self.post.type, self.post_type)
        self.assertEqual(self.post.organization, self.organization)
        self.assertEqual(self.post.categories.first(), self.category)
        self.assertEqual(str(self.post), 'Test Post')


class PostAttachmentTest(TestCase):
    """Test case for PostAttachment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.country = Country.objects.create(
            name='Test Country',
            code='TC'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TO',
            country=self.country
        )
        self.post_type = PostType.objects.create(
            name='Test Type',
            name_ar='نوع تجريبي'
        )
        self.post = Post.objects.create(
            title='Test Post',
            author=self.user,
            content='Test post content',
            type=self.post_type,
            organization=self.organization
        )
        self.temp_image = create_temp_image()
        self.attachment = PostAttachment.objects.create(
            post=self.post,
            file=self.temp_image,
            title='Test caption'
        )
    
    def test_attachment_creation(self):
        """Test attachment creation"""
        self.assertEqual(self.attachment.post, self.post)
        self.assertEqual(self.attachment.title, 'Test caption')
        self.assertTrue(self.attachment.file)
        self.assertTrue(str(self.attachment))


class BookmarkTest(TestCase):
    """Test case for Bookmark model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.country = Country.objects.create(
            name='Test Country',
            code='TC'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TO',
            country=self.country
        )
        self.post_type = PostType.objects.create(
            name='Test Type',
            name_ar='نوع تجريبي'
        )
        self.post = Post.objects.create(
            title='Test Post',
            author=self.user,
            content='Test post content',
            status='published',
            type=self.post_type,
            organization=self.organization
        )
        self.bookmark = Bookmark.objects.create(
            user=self.user,
            post=self.post,
            notes='Test bookmark notes'
        )
    
    def test_bookmark_creation(self):
        """Test bookmark creation"""
        self.assertEqual(self.bookmark.user, self.user)
        self.assertEqual(self.bookmark.post, self.post)
        self.assertEqual(self.bookmark.notes, 'Test bookmark notes')
        self.assertEqual(str(self.bookmark), f"{self.user.username} - {self.post.title}")


class APITest(APITestCase):
    """Test case for API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.country = Country.objects.create(
            name='Test Country',
            code='TC'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TO',
            country=self.country
        )
        self.post_type = PostType.objects.create(
            name='Test Type',
            name_ar='نوع تجريبي'
        )
        self.category = Category.objects.create(
            name='Test Category',
            name_ar='فئة تجريبية',
            slug='test-category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            author=self.user,
            content='Test post content',
            status='published',
            type=self.post_type,
            organization=self.organization
        )
        self.post.categories.add(self.category)
    
    def test_list_categories(self):
        """Test listing categories"""
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Category')
    
    def test_create_post(self):
        """Test creating a post"""
        url = reverse('post-list')
        data = {
            'title': 'New test post',
            'content': 'New test post content',
            'status': 'draft',
            'type_id': self.post_type.id,
            'organization': self.organization.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(response.data['content'], 'New test post content')
    
    def test_save_content(self):
        """Test bookmarking content"""
        url = reverse('bookmark-list')
        data = {
            'post_id': self.post.id,
            'notes': 'Test bookmark from API'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bookmark.objects.count(), 1)
