"""
Custom model managers with query optimization for the Qarar project.
"""
from django.db import models
from django.db.models import Q, F, Count, Prefetch, Exists, OuterRef
from django.utils import timezone
from typing import Dict, List, Any, Optional


class SoftDeleteManager(models.Manager):
    """
    Manager that automatically filters out soft-deleted objects.
    """
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        """Include soft-deleted objects."""
        return super().get_queryset()
    
    def deleted_only(self):
        """Only soft-deleted objects."""
        return super().get_queryset().filter(is_deleted=True)
    
    def delete_permanently(self):
        """Permanently delete all objects in the queryset."""
        return super().get_queryset().delete()


class OptimizedQueryMixin:
    """
    Mixin that provides common query optimizations.
    """
    
    def with_select_related(self, *fields):
        """Add select_related optimization."""
        return self.select_related(*fields)
    
    def with_prefetch_related(self, *fields):
        """Add prefetch_related optimization."""
        return self.prefetch_related(*fields)
    
    def with_annotations(self, **annotations):
        """Add annotations to the queryset."""
        return self.annotate(**annotations)
    
    def active(self):
        """Filter only active objects."""
        if hasattr(self.model, 'is_active'):
            return self.filter(is_active=True)
        return self
    
    def published(self):
        """Filter only published objects."""
        if hasattr(self.model, 'status'):
            return self.filter(status='published')
        return self


class CategoryManager(SoftDeleteManager, OptimizedQueryMixin):
    """
    Optimized manager for Category model.
    """
    
    def get_queryset(self):
        return super().get_queryset().select_related().prefetch_related(
            'subcategories'
        ).annotate(
            published_post_count=Count(
                'posts',
                filter=Q(posts__status='published', posts__is_deleted=False)
            )
        )
    
    def with_post_counts(self):
        """Include detailed post counts."""
        return self.annotate(
            total_posts=Count('posts', filter=Q(posts__is_deleted=False)),
            published_posts=Count(
                'posts',
                filter=Q(posts__status='published', posts__is_deleted=False)
            ),
            draft_posts=Count(
                'posts',
                filter=Q(posts__status='draft', posts__is_deleted=False)
            )
        )
    
    def with_subcategories(self):
        """Prefetch subcategories with optimizations."""
        return self.prefetch_related(
            Prefetch(
                'subcategories',
                queryset=self.model.subcategories.related.related_model.objects.filter(
                    is_deleted=False,
                    is_active=True
                ).annotate(
                    published_post_count=Count(
                        'posts',
                        filter=Q(posts__status='published', posts__is_deleted=False)
                    )
                ).order_by('order', 'name')
            )
        )
    
    def popular(self, limit=10):
        """Get most popular categories by post count."""
        return self.active().order_by('-published_post_count')[:limit]


class PostManager(SoftDeleteManager, OptimizedQueryMixin):
    """
    Optimized manager for Post model with comprehensive query optimizations.
    """
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'author',
            'type',
            'organization',
            'subsidiary'
        )
    
    def optimized(self):
        """Fully optimized queryset for list views."""
        return self.select_related(
            'author',
            'type',
            'organization',
            'subsidiary'
        ).prefetch_related(
            'categories',
            'subcategories',
            'hashtags',
            Prefetch(
                'attachments',
                queryset=self.model.attachments.related.related_model.objects.filter(
                    is_deleted=False,
                    is_public=True
                ).order_by('order', 'created_at')
            )
        ).annotate(
            attachment_count=Count(
                'attachments',
                filter=Q(attachments__is_deleted=False, attachments__is_public=True)
            ),
            category_count=Count('categories', filter=Q(categories__is_deleted=False)),
            hashtag_count=Count('hashtags', filter=Q(hashtags__is_deleted=False))
        )
    
    def for_api_list(self):
        """Optimized for API list endpoints."""
        return self.optimized().only(
            'id', 'title', 'title_ar', 'summary', 'summary_ar',
            'slug', 'status', 'created_at', 'published_at', 'view_count',
            'is_featured', 'is_urgent', 'priority',
            'author__id', 'author__username', 'author__first_name', 'author__last_name',
            'type__id', 'type__name', 'type__name_ar', 'type__color',
            'organization__id', 'organization__name', 'organization__name_ar'
        )
    
    def for_api_detail(self):
        """Optimized for API detail endpoints."""
        return self.optimized()
    
    def with_bookmark_status(self, user):
        """Annotate with bookmark status for a specific user."""
        if user and user.is_authenticated:
            from apps.content.models.bookmark import Bookmark
            return self.annotate(
                is_bookmarked=Exists(
                    Bookmark.objects.filter(
                        user=user,
                        post=OuterRef('pk'),
                        is_deleted=False
                    )
                )
            )
        return self.annotate(is_bookmarked=models.Value(False, output_field=models.BooleanField()))
    
    def published(self):
        """Get only published posts."""
        return self.filter(status='published')
    
    def featured(self):
        """Get featured posts."""
        return self.filter(is_featured=True)
    
    def urgent(self):
        """Get urgent posts."""
        return self.filter(is_urgent=True)
    
    def by_organization(self, organization_id):
        """Filter by organization."""
        return self.filter(organization_id=organization_id)
    
    def by_type(self, post_type_id):
        """Filter by post type."""
        return self.filter(type_id=post_type_id)
    
    def by_category(self, category_id):
        """Filter by category."""
        return self.filter(categories__id=category_id)
    
    def by_hashtag(self, hashtag_id):
        """Filter by hashtag."""
        return self.filter(hashtags__id=hashtag_id)
    
    def search_text(self, query):
        """Full-text search across title and content."""
        if not query:
            return self
        
        search_query = Q(title__icontains=query) | Q(content__icontains=query) | \
                      Q(title_ar__icontains=query) | Q(content_ar__icontains=query) | \
                      Q(summary__icontains=query) | Q(summary_ar__icontains=query)
        
        return self.filter(search_query)
    
    def recent(self, days=30):
        """Get recent posts within specified days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def popular(self, limit=10):
        """Get most popular posts by view count."""
        return self.published().order_by('-view_count')[:limit]
    
    def trending(self, days=7, limit=10):
        """Get trending posts based on recent views."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.published().filter(
            created_at__gte=cutoff_date
        ).order_by('-view_count', '-created_at')[:limit]
    
    def for_feed(self, user=None, limit=20):
        """Optimized feed query."""
        queryset = self.published().for_api_list().order_by('-priority', '-published_at')
        
        if user:
            queryset = queryset.with_bookmark_status(user)
        
        return queryset[:limit]


class HashTagManager(SoftDeleteManager, OptimizedQueryMixin):
    """
    Optimized manager for HashTag model.
    """
    
    def get_queryset(self):
        return super().get_queryset().annotate(
            published_post_count=Count(
                'posts',
                filter=Q(posts__status='published', posts__is_deleted=False)
            )
        )
    
    def trending(self, limit=10):
        """Get trending hashtags."""
        return self.filter(is_trending=True).active().order_by(
            '-published_post_count', 'name'
        )[:limit]
    
    def popular(self, limit=20):
        """Get popular hashtags by post count."""
        return self.active().order_by('-published_post_count', 'name')[:limit]
    
    def search(self, query, limit=10):
        """Search hashtags by name."""
        return self.active().filter(
            name__icontains=query
        ).order_by('-published_post_count', 'name')[:limit]
    
    def with_recent_activity(self, days=7):
        """Get hashtags with recent activity."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(last_used__gte=cutoff_date)


class BookmarkManager(SoftDeleteManager, OptimizedQueryMixin):
    """
    Optimized manager for Bookmark model.
    """
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user',
            'post',
            'post__author',
            'post__type',
            'post__organization'
        )
    
    def for_user(self, user):
        """Get bookmarks for a specific user."""
        return self.filter(user=user)
    
    def public(self):
        """Get public bookmarks."""
        return self.filter(is_private=False)
    
    def with_post_details(self):
        """Include full post details."""
        return self.select_related(
            'post__author',
            'post__type', 
            'post__organization',
            'post__subsidiary'
        ).prefetch_related(
            'post__categories',
            'post__hashtags'
        )


class PostAttachmentManager(SoftDeleteManager, OptimizedQueryMixin):
    """
    Optimized manager for PostAttachment model.
    """
    
    def get_queryset(self):
        return super().get_queryset().select_related('post')
    
    def public(self):
        """Get public attachments."""
        return self.filter(is_public=True)
    
    def for_post(self, post_id):
        """Get attachments for a specific post."""
        return self.filter(post_id=post_id)
    
    def images(self):
        """Get only image attachments."""
        return self.filter(file_type__startswith='image/')
    
    def documents(self):
        """Get only document attachments."""
        document_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'application/rtf',
        ]
        return self.filter(file_type__in=document_types)
    
    def ordered(self):
        """Get attachments in display order."""
        return self.order_by('order', 'created_at')


# Custom QuerySet classes for even more control
class PostQuerySet(models.QuerySet):
    """
    Custom QuerySet for Post model with advanced filtering capabilities.
    """
    
    def published(self):
        return self.filter(status='published', is_deleted=False)
    
    def for_user_feed(self, user, limit=20):
        """Generate personalized feed for user."""
        # This could include ML-based recommendations in the future
        queryset = self.published().select_related(
            'author', 'type', 'organization'
        ).order_by('-priority', '-published_at')
        
        # Add user-specific annotations
        if user and user.is_authenticated:
            queryset = queryset.annotate(
                is_bookmarked=Exists(
                    user.bookmarks.filter(post=OuterRef('pk'), is_deleted=False)
                )
            )
        
        return queryset[:limit]
    
    def similar_to(self, post, limit=5):
        """Find posts similar to the given post."""
        # Simple similarity based on categories and hashtags
        return self.published().filter(
            Q(categories__in=post.categories.all()) |
            Q(hashtags__in=post.hashtags.all())
        ).exclude(id=post.id).distinct().order_by('-view_count')[:limit]


# Add custom managers to models by importing in __init__.py or models.py