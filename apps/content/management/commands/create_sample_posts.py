import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils import timezone
from pathlib import Path
import tempfile
from urllib.request import urlopen
import os

from apps.content.models import Post, PostAttachment, Category

User = get_user_model()

# Sample paragraphs for post content
SAMPLE_PARAGRAPHS = [
    "The legal status of displaced Syrians involves complex questions of international law and refugee protection standards.",
    "Urban reconstruction in Syrian cities requires careful planning and community involvement to ensure sustainable outcomes.",
    "Access to education remains a critical challenge for Syrian children in displacement contexts across the region.",
    "Healthcare systems in Syria have been severely impacted by years of conflict, creating significant gaps in service provision.",
    "Traditional Syrian crafts represent an important cultural heritage that connects communities across borders.",
    "Agricultural recovery in rural Syria faces challenges related to water access, infrastructure damage, and market integration.",
    "Documentation issues create barriers for Syrians seeking to establish legal identity and access essential services.",
    "Renewable energy solutions offer promising approaches to address electricity shortages in various Syrian contexts.",
    "Women's economic participation in Syrian communities has transformed dramatically during the years of displacement.",
    "Digital literacy programs provide important opportunities for Syrian youth to develop skills for the modern economy."
]

# Sample image URLs for attachments
SAMPLE_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1523731407965-2430cd12f5e4",
    "https://images.unsplash.com/photo-1558642983-2e9b0629b7f0",
    "https://images.unsplash.com/photo-1598395927056-8d895e701c3b"
]

# Sample video URLs
SAMPLE_VIDEO_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://vimeo.com/565486457"
]

class Command(BaseCommand):
    help = 'Create sample posts with attachments'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of posts to create')
        parser.add_argument('--username', type=str, help='Username of the post author')

    def handle(self, *args, **options):
        count = options['count']
        username = options.get('username')
        
        # Get or create categories
        categories = self._ensure_categories()
        
        # Get author
        if username:
            try:
                author = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with username {username} does not exist'))
                return
        else:
            # Use first admin user
            author = User.objects.filter(is_staff=True).first()
            if not author:
                self.stdout.write(self.style.ERROR('No admin users found. Please create one or specify a username.'))
                return
        
        # Create posts
        created_posts = []
        for i in range(count):
            content = random.choice(SAMPLE_PARAGRAPHS)
            
            post = Post.objects.create(
                author=author,
                content=content,
                status='published',
                published_at=timezone.now()
            )
            
            # Add random categories (1-3)
            cat_count = random.randint(1, min(3, len(categories)))
            selected_cats = random.sample(list(categories), cat_count)
            for category in selected_cats:
                post.categories.add(category)
            
            created_posts.append(post)
            self.stdout.write(self.style.SUCCESS(f'Created post {i+1}/{count}'))
            
            # Add attachments
            self._add_attachments(post)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(created_posts)} posts'))

    def _ensure_categories(self):
        """Ensure we have categories to use"""
        category_names = [
            'Legal', 'Education', 'Healthcare', 'Culture', 
            'Economy', 'Technology', 'Human Rights', 'Infrastructure'
        ]
        
        categories = []
        for name in category_names:
            slug = name.lower()
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slug}
            )
            categories.append(category)
            
            if created:
                self.stdout.write(f'Created category: {name}')
                
        return categories

    def _add_attachments(self, post):
        """Add random attachments to posts"""
        # Decide how many attachments (0-3)
        attachment_count = random.randint(0, 3)
        
        for i in range(attachment_count):
            # Choose attachment type
            attachment_type = random.choice(['image', 'video', 'file'])
            
            if attachment_type == 'image':
                # Create image attachment
                image_url = random.choice(SAMPLE_IMAGE_URLS)
                self._create_image_attachment(post, image_url, i)
            elif attachment_type == 'video':
                # Create video attachment
                video_url = random.choice(SAMPLE_VIDEO_URLS)
                PostAttachment.objects.create(
                    post=post,
                    attachment_type='video',
                    is_external=True,
                    external_url=video_url,
                    caption=f"Sample video {i+1}",
                    order=i
                )
            elif attachment_type == 'file':
                # Create a placeholder file attachment
                PostAttachment.objects.create(
                    post=post,
                    attachment_type='file',
                    is_external=True,
                    external_url="https://example.com/sample.pdf",
                    caption=f"Sample document {i+1}",
                    order=i
                )

    def _create_image_attachment(self, post, image_url, order):
        """Create an image attachment from a URL"""
        try:
            # We'll just set the external URL rather than downloading and storing the image
            PostAttachment.objects.create(
                post=post,
                attachment_type='image',
                is_external=True,
                external_url=image_url,
                caption=f"Sample image {order+1}",
                order=order
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error creating image attachment: {str(e)}')) 