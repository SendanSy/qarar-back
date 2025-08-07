from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from apps.core.models import BaseModel
from apps.core.managers import PostManager, CategoryManager, PostAttachmentManager
from apps.producers.models import Organization, Subsidiary, Department
from .classification import Category, SubCategory, HashTag


class PostType(BaseModel):
    """
    Types of posts (e.g., قرار, تعميم, etc.)
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )
    name_ar = models.CharField(
        max_length=100,
        verbose_name=_('Arabic Name')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Description')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )

    class Meta:
        verbose_name = _('Post Type')
        verbose_name_plural = _('Post Types')
        ordering = ['name']

    def __str__(self):
        return self.name_ar


class Post(BaseModel):
    """
    Main post model with enhanced relationships and metadata
    """
    # Basic Fields
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    title_ar = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Arabic Title')
    )
    content = models.TextField(
        verbose_name=_('Content'),
        blank=True,
    )
    content_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Content')
    )
    summary = models.TextField(
        blank=True,
        verbose_name=_('Summary')
    )
    summary_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Summary')
    )
    
    # Relations
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_posts',
        verbose_name=_('Author')
    )
    type = models.ForeignKey(
        PostType,
        on_delete=models.PROTECT,
        related_name='posts',
        verbose_name=_('Post Type')
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='posts',
        verbose_name=_('Organization')
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name=_('Subsidiary')
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name=_('Department')
    )
    
    # Classifications
    categories = models.ManyToManyField(
        Category,
        related_name='posts',
        blank=True,
        verbose_name=_('Categories')
    )
    subcategories = models.ManyToManyField(
        SubCategory,
        related_name='posts',
        blank=True,
        verbose_name=_('Sub Categories')
    )
    hashtags = models.ManyToManyField(
        HashTag,
        related_name='posts',
        blank=True,
        verbose_name=_('Hashtags')
    )
    
    # Publication status
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('pending', _('Pending Review')),
        ('published', _('Published')),
        ('archived', _('Archived')),
        ('rejected', _('Rejected')),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    # Timestamps
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Published At')
    )
    
    # Analytics
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('View Count')
    )
    
    # SEO and sharing
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_('Slug')
    )
    meta_description = models.TextField(
        blank=True,
        verbose_name=_('Meta Description')
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Meta Keywords')
    )
    
    # Managers
    objects = PostManager()

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['published_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['view_count']),
        ]

    def __str__(self):
        return self.title_ar

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            
        # Save the post first
        super().save(*args, **kwargs)
        
        # Extract and process hashtags from content
        self._process_hashtags()

    def _process_hashtags(self):
        """
        Extract hashtags from content and content_ar, create hashtag objects,
        and link them to this post. Updates post counts for hashtags.
        """
        # Get current hashtags for this post
        current_hashtags = set(self.hashtags.values_list('name', flat=True))
        
        # Extract hashtags from both content fields
        all_hashtags = set()
        
        # Extract from English content
        if self.content:
            hashtags_en = HashTag.extract_from_content(self.content)
            all_hashtags.update(hashtags_en)
        
        # Extract from Arabic content
        if self.content_ar:
            hashtags_ar = HashTag.extract_from_content(self.content_ar)
            all_hashtags.update(hashtags_ar)
        
        # Extract from summary fields as well
        if self.summary:
            hashtags_summary = HashTag.extract_from_content(self.summary)
            all_hashtags.update(hashtags_summary)
            
        if self.summary_ar:
            hashtags_summary_ar = HashTag.extract_from_content(self.summary_ar)
            all_hashtags.update(hashtags_summary_ar)
        
        # Find hashtags to add and remove
        hashtags_to_add = all_hashtags - current_hashtags
        hashtags_to_remove = current_hashtags - all_hashtags
        
        # Remove old hashtags
        if hashtags_to_remove:
            old_hashtags = HashTag.objects.filter(name__in=hashtags_to_remove)
            self.hashtags.remove(*old_hashtags)
            
            # Update post counts for removed hashtags
            for hashtag in old_hashtags:
                hashtag.update_post_count()
        
        # Add new hashtags
        if hashtags_to_add:
            new_hashtag_objects = []
            for tag_name in hashtags_to_add:
                hashtag, created = HashTag.objects.get_or_create(
                    name=tag_name,
                    defaults={
                        'slug': tag_name.lower().replace(' ', '-'),
                        'description': f'Posts tagged with #{tag_name}',
                        'is_active': True,
                        'order': 0
                    }
                )
                new_hashtag_objects.append(hashtag)
            
            # Add hashtags to this post
            self.hashtags.add(*new_hashtag_objects)
            
            # Update post counts for new/existing hashtags
            for hashtag in new_hashtag_objects:
                hashtag.update_post_count()

    def increment_view_count(self):
        """Increment the view count safely"""
        self.__class__.objects.filter(id=self.id).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db()

    @property
    def is_published(self):
        """Check if the post is published"""
        return self.status == 'published'

    @property
    def reading_time(self):
        """Calculate estimated reading time in minutes"""
        words_per_minute = 200
        word_count = len(self.content.split())
        return max(1, round(word_count / words_per_minute))

    def publish(self):
        """Publish the post"""
        self.status = 'published'
        if not self.published_at:
            self.published_at = timezone.now()
        self.save()

    def get_display_title(self, language='en'):
        """Get title based on language preference"""
        if language == 'ar' and self.title_ar:
            return self.title_ar
        return self.title

    def get_display_content(self, language='en'):
        """Get content based on language preference"""
        if language == 'ar' and self.content_ar:
            return self.content_ar
        return self.content


class PostAttachment(BaseModel):
    """
    Model for managing post attachments
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Post')
    )
    file = models.FileField(
        upload_to='post_attachments/%Y/%m/%d/',
        verbose_name=_('File')
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Title')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    file_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('File Type')
    )
    size = models.PositiveIntegerField(
        default=0,
        verbose_name=_('File Size')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Display Order')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Is Public'),
        help_text=_('Whether this attachment is publicly visible')
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Download Count'),
        help_text=_('Number of times this attachment has been downloaded')
    )

    # Manager
    objects = PostAttachmentManager()

    class Meta:
        verbose_name = _('Post Attachment')
        verbose_name_plural = _('Post Attachments')
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['file_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title or self.file.name} - {self.post.title}"

    def save(self, *args, **kwargs):
        # Update file size if not set
        if not self.size and self.file:
            self.size = self.file.size
        # Set file type if not set
        if not self.file_type and self.file:
            import mimetypes
            self.file_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
        super().save(*args, **kwargs)

    @property
    def is_document(self):
        """Check if the attachment is a document"""
        document_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        return self.file_type in document_types

    @property
    def is_image(self):
        """Check if the attachment is an image"""
        return self.file_type.startswith('image/') if self.file_type else False

    @property
    def formatted_size(self):
        """Return formatted file size"""
        if self.size < 1024:
            return f"{self.size}.0 B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"

    def increment_download_count(self):
        """Increment the download count safely"""
        self.__class__.objects.filter(id=self.id).update(download_count=models.F('download_count') + 1)
        self.refresh_from_db(fields=['download_count'])


# Through models for many-to-many relationships with additional fields
class PostCategory(models.Model):
    """Through model for Post-Category relationship."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'category')
        verbose_name = _('Post Category')
        verbose_name_plural = _('Post Categories')


class PostSubCategory(models.Model):
    """Through model for Post-SubCategory relationship."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'subcategory')
        verbose_name = _('Post Sub Category')
        verbose_name_plural = _('Post Sub Categories')


class PostHashTag(models.Model):
    """Through model for Post-HashTag relationship."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    hashtag = models.ForeignKey(HashTag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'hashtag')
        verbose_name = _('Post HashTag')
        verbose_name_plural = _('Post HashTags')