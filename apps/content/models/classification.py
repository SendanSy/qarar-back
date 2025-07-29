from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from apps.core.models import CategoryBaseModel
from apps.core.managers import CategoryManager, HashTagManager, SoftDeleteManager
from apps.core.validators import hashtag_validator
import re


class Category(CategoryBaseModel):
    """
    Main categories for content classification
    """
    name_ar = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Arabic Name'),
        help_text=_('Arabic name of the category')
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Description'),
        help_text=_('Arabic description of the category')
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Icon Class'),
        help_text=_('CSS icon class for the category')
    )
    post_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Post Count'),
        help_text=_('Number of posts in this category')
    )
    
    # Manager
    objects = CategoryManager()
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'order']),
            models.Index(fields=['post_count']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(is_deleted=False),
                name='unique_category_name'
            ),
            models.UniqueConstraint(
                fields=['name_ar'],
                condition=models.Q(is_deleted=False),
                name='unique_category_name_ar'
            ),
            models.UniqueConstraint(
                fields=['slug'],
                condition=models.Q(is_deleted=False),
                name='unique_category_slug'
            ),
        ]
    
    def clean(self):
        super().clean()
        if not self.name and not self.name_ar:
            raise ValidationError(_('Either name or Arabic name must be provided.'))
    
    def update_post_count(self):
        """Update the post count for this category."""
        self.post_count = self.posts.filter(status='published', is_deleted=False).count()
        self.save(update_fields=['post_count'])


class SubCategory(CategoryBaseModel):
    """
    Sub-categories that belong to main categories
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name=_('Category'),
        help_text=_('Parent category')
    )
    name_ar = models.CharField(
        max_length=100,
        verbose_name=_('Arabic Name'),
        help_text=_('Arabic name of the sub-category')
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Description'),
        help_text=_('Arabic description of the sub-category')
    )
    post_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Post Count'),
        help_text=_('Number of posts in this sub-category')
    )
    
    # Manager
    objects = SoftDeleteManager()
    
    class Meta:
        verbose_name = _('Sub Category')
        verbose_name_plural = _('Sub Categories')
        ordering = ['category', 'order', 'name']
        indexes = [
            models.Index(fields=['category', 'slug']),
            models.Index(fields=['is_active', 'order']),
            models.Index(fields=['post_count']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'name'],
                condition=models.Q(is_deleted=False),
                name='unique_subcategory_name_per_category'
            ),
            models.UniqueConstraint(
                fields=['category', 'slug'],
                condition=models.Q(is_deleted=False),
                name='unique_subcategory_slug_per_category'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    def clean(self):
        super().clean()
        if not self.name and not self.name_ar:
            raise ValidationError(_('Either name or Arabic name must be provided.'))
    
    def update_post_count(self):
        """Update the post count for this sub-category."""
        self.post_count = self.posts.filter(status='published', is_deleted=False).count()
        self.save(update_fields=['post_count'])


class HashTag(CategoryBaseModel):
    """
    Hashtags for content classification, automatically extracted from content
    """
    post_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Post Count'),
        help_text=_('Number of posts using this hashtag')
    )
    is_trending = models.BooleanField(
        default=False,
        verbose_name=_('Is Trending'),
        help_text=_('Whether this hashtag is currently trending')
    )
    last_used = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Used'),
        help_text=_('When this hashtag was last used')
    )
    
    # Manager
    objects = HashTagManager()
    
    class Meta:
        verbose_name = _('Hashtag')
        verbose_name_plural = _('Hashtags')
        ordering = ['-post_count', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['post_count']),
            models.Index(fields=['is_trending']),
            models.Index(fields=['last_used']),
            models.Index(fields=['is_active', 'post_count']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(is_deleted=False),
                name='unique_hashtag_name'
            ),
            models.UniqueConstraint(
                fields=['slug'],
                condition=models.Q(is_deleted=False),
                name='unique_hashtag_slug'
            ),
        ]
    
    def __str__(self):
        return f"#{self.name}"
    
    def clean(self):
        super().clean()
        # Validate hashtag format
        if self.name:
            hashtag_validator(self.name)
    
    def save(self, *args, **kwargs):
        # Clean the hashtag name (remove # if present)
        if self.name and self.name.startswith('#'):
            self.name = self.name[1:]
        super().save(*args, **kwargs)
    
    def update_post_count(self):
        """Update the post count for this hashtag."""
        self.post_count = self.posts.filter(status='published', is_deleted=False).count()
        self.save(update_fields=['post_count'])
    
    def mark_trending(self):
        """Mark this hashtag as trending."""
        self.is_trending = True
        self.save(update_fields=['is_trending'])
    
    def unmark_trending(self):
        """Remove trending status from this hashtag."""
        self.is_trending = False
        self.save(update_fields=['is_trending'])
    
    @classmethod
    def extract_from_content(cls, content):
        """
        Extract hashtags from content text with comprehensive validation.
        Supports English, Arabic, and mixed content.
        Returns a list of cleaned hashtag names.
        """
        if not content:
            return []
        
        # Enhanced pattern to support:
        # - English letters (a-z, A-Z)
        # - Arabic letters (\u0600-\u06FF)
        # - Numbers (0-9)
        # - Underscores (_)
        # - Minimum length of 2 characters
        hashtag_pattern = r'#([a-zA-Z0-9_\u0600-\u06FF]{2,50})'
        hashtags = re.findall(hashtag_pattern, content)
        
        # Clean and validate hashtags
        cleaned_hashtags = []
        for tag in hashtags:
            try:
                # Additional cleaning
                tag = tag.strip()
                
                # Skip if too short or too long
                if len(tag) < 2 or len(tag) > 50:
                    continue
                
                # Skip if only numbers or underscores
                if tag.replace('_', '').replace(' ', '').isdigit():
                    continue
                
                # Validate using custom validator
                hashtag_validator(tag)
                
                # Convert to lowercase for consistency (except Arabic)
                if re.match(r'^[a-zA-Z0-9_]+$', tag):
                    tag = tag.lower()
                
                cleaned_hashtags.append(tag)
                
            except ValidationError:
                # Skip invalid hashtags
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in cleaned_hashtags:
            if tag not in seen:
                seen.add(tag)
                unique_hashtags.append(tag)
        
        return unique_hashtags
    
    def get_posts(self, status='published', limit=None):
        """
        Get posts that are tagged with this hashtag.
        
        Args:
            status: Filter by post status (default: 'published')
            limit: Limit number of posts returned
        
        Returns:
            QuerySet of posts
        """
        queryset = self.posts.filter(status=status).select_related(
            'author', 'type', 'organization'
        ).prefetch_related('categories', 'hashtags').order_by('-published_at')
        
        if limit:
            queryset = queryset[:limit]
            
        return queryset
    
    @classmethod
    def get_trending_hashtags(cls, limit=10):
        """
        Get trending hashtags ordered by usage and recent activity.
        
        Args:
            limit: Number of hashtags to return
            
        Returns:
            QuerySet of trending hashtags
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Get hashtags used in the last 7 days
        recent_date = timezone.now() - timedelta(days=7)
        
        return cls.objects.filter(
            is_active=True,
            last_used__gte=recent_date,
            post_count__gt=0
        ).order_by('-post_count', '-last_used')[:limit]
    
    @classmethod
    def get_popular_hashtags(cls, limit=20):
        """
        Get popular hashtags ordered by total post count.
        
        Args:
            limit: Number of hashtags to return
            
        Returns:
            QuerySet of popular hashtags
        """
        return cls.objects.filter(
            is_active=True,
            post_count__gt=0
        ).order_by('-post_count', 'name')[:limit] 