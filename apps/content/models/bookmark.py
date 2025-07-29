"""
Bookmark model for user content saving functionality.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel
from apps.core.managers import BookmarkManager, SoftDeleteManager
from .post import Post


class Bookmark(BaseModel):
    """
    Model for user bookmarks/saved content.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name=_('User'),
        help_text=_('User who bookmarked the content')
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name=_('Post'),
        help_text=_('Bookmarked post')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Personal notes about the bookmark')
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Tags'),
        help_text=_('Comma-separated tags for organizing bookmarks')
    )
    is_private = models.BooleanField(
        default=True,
        verbose_name=_('Is Private'),
        help_text=_('Whether this bookmark is private to the user')
    )
    
    # Manager
    objects = BookmarkManager()
    
    class Meta:
        verbose_name = _('Bookmark')
        verbose_name_plural = _('Bookmarks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['is_private']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                condition=models.Q(is_deleted=False),
                name='unique_user_post_bookmark'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.post.title}"
    
    def clean(self):
        """Validate the bookmark."""
        super().clean()
        
        # Check if post is published (can't bookmark drafts)
        if self.post and not self.post.is_published:
            raise ValidationError(_('Cannot bookmark unpublished content.'))
    
    def get_tag_list(self):
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tag_list(self, tag_list):
        """Set tags from a list."""
        self.tags = ', '.join(tag_list) if tag_list else ''


class BookmarkCollection(BaseModel):
    """
    Model for organizing bookmarks into collections.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmark_collections',
        verbose_name=_('User'),
        help_text=_('User who owns the collection')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Name of the collection')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Description of the collection')
    )
    bookmarks = models.ManyToManyField(
        Bookmark,
        through='BookmarkCollectionItem',
        related_name='collections',
        blank=True,
        verbose_name=_('Bookmarks')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Is Public'),
        help_text=_('Whether this collection is publicly visible')
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=_('Color'),
        help_text=_('Hex color code for the collection')
    )
    
    # Manager
    objects = SoftDeleteManager()
    
    class Meta:
        verbose_name = _('Bookmark Collection')
        verbose_name_plural = _('Bookmark Collections')
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'name']),
            models.Index(fields=['is_public']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                condition=models.Q(is_deleted=False),
                name='unique_user_collection_name'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def clean(self):
        """Validate the collection."""
        super().clean()
        
        # Validate color format
        if self.color and not self.color.startswith('#'):
            raise ValidationError(_('Color must be a valid hex color code.'))
    
    @property
    def bookmark_count(self):
        """Get the number of bookmarks in this collection."""
        return self.collection_items.filter(
            bookmark__is_deleted=False
        ).count()


class BookmarkCollectionItem(models.Model):
    """
    Through model for bookmark collections.
    """
    collection = models.ForeignKey(
        BookmarkCollection,
        on_delete=models.CASCADE,
        related_name='collection_items',
        verbose_name=_('Collection')
    )
    bookmark = models.ForeignKey(
        Bookmark,
        on_delete=models.CASCADE,
        related_name='collection_items',
        verbose_name=_('Bookmark')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Order of the bookmark in the collection')
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Added At'),
        help_text=_('When the bookmark was added to the collection')
    )
    
    class Meta:
        unique_together = ('collection', 'bookmark')
        ordering = ['order', 'added_at']
        verbose_name = _('Bookmark Collection Item')
        verbose_name_plural = _('Bookmark Collection Items')
        indexes = [
            models.Index(fields=['collection', 'order']),
            models.Index(fields=['added_at']),
        ]
    
    def __str__(self):
        return f"{self.collection.name} - {self.bookmark.post.title}"