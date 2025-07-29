"""
Core models with base classes for the Qarar project.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


class UUIDMixin(models.Model):
    """
    Mixin to add UUID primary key to models.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    """
    Mixin to add created and updated timestamps to models.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
        help_text=_('Date and time when the record was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At'),
        help_text=_('Date and time when the record was last updated')
    )
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete functionality to models.
    """
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_('Is Deleted'),
        help_text=_('Whether this record is soft deleted')
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Deleted At'),
        help_text=_('Date and time when the record was deleted')
    )
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """
        Soft delete the object by setting is_deleted=True and deleted_at timestamp.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=['is_deleted', 'deleted_at'])
    
    def hard_delete(self, using=None, keep_parents=False):
        """
        Permanently delete the object from the database.
        """
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """
        Restore a soft-deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class BilingualMixin(models.Model):
    """
    Mixin to add bilingual support to models.
    """
    language_code = models.CharField(
        max_length=7,
        choices=[
            ('en', _('English')),
            ('ar', _('Arabic')),
        ],
        default='en',
        verbose_name=_('Language'),
        help_text=_('Primary language of the content')
    )
    
    class Meta:
        abstract = True


class SEOMixin(models.Model):
    """
    Mixin to add SEO fields to models.
    """
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly version of the title')
    )
    meta_description = models.TextField(
        max_length=160,
        blank=True,
        verbose_name=_('Meta Description'),
        help_text=_('Brief description for search engines (max 160 characters)')
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Meta Keywords'),
        help_text=_('Comma-separated keywords for search engines')
    )
    
    class Meta:
        abstract = True
    
    def clean(self):
        """
        Validate SEO fields.
        """
        super().clean()
        if self.meta_description and len(self.meta_description) > 160:
            raise ValidationError({
                'meta_description': _('Meta description must be 160 characters or less.')
            })


class PublishableMixin(models.Model):
    """
    Mixin to add publishing functionality to models.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending Review')),
        ('published', _('Published')),
        ('archived', _('Archived')),
        ('rejected', _('Rejected')),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status'),
        help_text=_('Publication status of the content')
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Published At'),
        help_text=_('Date and time when the content was published')
    )
    
    class Meta:
        abstract = True
    
    @property
    def is_published(self):
        """Check if the content is published."""
        return self.status == 'published'
    
    @property
    def is_draft(self):
        """Check if the content is in draft status."""
        return self.status == 'draft'
    
    def publish(self, user=None):
        """
        Publish the content.
        """
        if self.status != 'published':
            self.status = 'published'
            self.published_at = timezone.now()
            self.save(update_fields=['status', 'published_at'])
    
    def unpublish(self):
        """
        Unpublish the content.
        """
        if self.status == 'published':
            self.status = 'draft'
            self.published_at = None
            self.save(update_fields=['status', 'published_at'])


class ViewTrackingMixin(models.Model):
    """
    Mixin to add view tracking functionality to models.
    """
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('View Count'),
        help_text=_('Number of times this content has been viewed')
    )
    last_viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last Viewed At'),
        help_text=_('Date and time when the content was last viewed')
    )
    
    class Meta:
        abstract = True
    
    def increment_view_count(self):
        """
        Increment the view count safely using F expressions.
        """
        self.__class__.objects.filter(id=self.id).update(
            view_count=models.F('view_count') + 1,
            last_viewed_at=timezone.now()
        )
        self.refresh_from_db(fields=['view_count', 'last_viewed_at'])


class AuditMixin(models.Model):
    """
    Mixin to add audit trail functionality to models.
    """
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        null=True,
        blank=True,
        verbose_name=_('Created By'),
        help_text=_('User who created this record')
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='%(class)s_updated',
        null=True,
        blank=True,
        verbose_name=_('Updated By'),
        help_text=_('User who last updated this record')
    )
    
    class Meta:
        abstract = True


class BaseModel(UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Base model with UUID, timestamps, and soft delete functionality.
    """
    class Meta:
        abstract = True


class ContentBaseModel(BaseModel, BilingualMixin, SEOMixin, PublishableMixin, ViewTrackingMixin, AuditMixin):
    """
    Base model for content with all common functionality.
    """
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title of the content')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Brief description of the content')
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['view_count']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """
        Validate the model fields.
        """
        super().clean()
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()


class CategoryBaseModel(BaseModel, BilingualMixin, SEOMixin):
    """
    Base model for categories and taxonomies.
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Name of the category')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Description of the category')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Whether this category is active')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Order for display purposes')
    )
    
    class Meta:
        abstract = True
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'order']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Auto-generate slug if not provided.
        """
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)