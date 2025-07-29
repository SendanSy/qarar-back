"""
Service classes for content management operations.
"""
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, F, Count, Prefetch

from apps.core.services import CRUDService, PublishableService, ViewTrackingService, SearchService
from apps.core.exceptions import BusinessLogicError, NotFoundError, PermissionDeniedError
from .models.post import Post, PostType, PostAttachment, PostCategory, PostSubCategory, PostHashTag
from .models.classification import Category, SubCategory, HashTag
from apps.producers.models import Organization, Subsidiary

User = get_user_model()


class PostTypeService(CRUDService):
    """Service for managing post types."""
    
    model = PostType
    
    def get_queryset(self):
        """Get active post types with post count."""
        return self.model.objects.filter(is_deleted=False).annotate(
            active_post_count=Count('posts', filter=Q(posts__status='published', posts__is_deleted=False))
        )
    
    def get_active_types(self) -> List[PostType]:
        """Get all active post types."""
        return self.list({'is_active': True}, ['order', 'name'])
    
    def update_post_counts(self) -> None:
        """Update post counts for all post types."""
        for post_type in self.model.objects.filter(is_deleted=False):
            post_type.update_post_count()


class CategoryService(CRUDService):
    """Service for managing categories."""
    
    model = Category
    
    def get_queryset(self):
        """Get categories with subcategories and post counts."""
        return self.model.objects.filter(is_deleted=False).prefetch_related(
            Prefetch('subcategories', queryset=SubCategory.objects.filter(is_deleted=False, is_active=True))
        ).annotate(
            active_post_count=Count('posts', filter=Q(posts__status='published', posts__is_deleted=False))
        )
    
    def get_active_categories(self) -> List[Category]:
        """Get all active categories with their subcategories."""
        return self.list({'is_active': True}, ['order', 'name'])
    
    def get_category_with_posts(self, category_id: Any, limit: int = 10) -> Dict[str, Any]:
        """Get category with its recent posts."""
        category = self.get_by_id(category_id)
        
        recent_posts = Post.objects.filter(
            categories=category,
            status='published',
            is_deleted=False
        ).select_related('author', 'type', 'organization').order_by('-published_at')[:limit]
        
        return {
            'category': category,
            'posts': list(recent_posts),
            'total_posts': category.post_count
        }


class HashTagService(CRUDService):
    """Service for managing hashtags."""
    
    model = HashTag
    
    def get_queryset(self):
        """Get hashtags with post counts."""
        return self.model.objects.filter(is_deleted=False).annotate(
            active_post_count=Count('posts', filter=Q(posts__status='published', posts__is_deleted=False))
        )
    
    def get_trending_hashtags(self, limit: int = 10) -> List[HashTag]:
        """Get trending hashtags."""
        return self.list({'is_trending': True, 'is_active': True}, ['-post_count', 'name'])[:limit]
    
    def get_popular_hashtags(self, limit: int = 20) -> List[HashTag]:
        """Get popular hashtags by post count."""
        return self.list({'is_active': True}, ['-post_count', 'name'])[:limit]
    
    def search_hashtags(self, query: str, limit: int = 10) -> List[HashTag]:
        """Search hashtags by name."""
        return list(
            self.get_queryset().filter(
                name__icontains=query,
                is_active=True
            ).order_by('-post_count', 'name')[:limit]
        )
    
    def update_trending_status(self, min_posts: int = 5, days: int = 7) -> None:
        """Update trending status based on recent activity."""
        from datetime import timedelta
        
        # Calculate trending threshold
        recent_date = timezone.now() - timedelta(days=days)
        
        # Mark as trending
        trending_hashtags = self.model.objects.filter(
            is_deleted=False,
            post_count__gte=min_posts,
            last_used__gte=recent_date
        )
        trending_hashtags.update(is_trending=True)
        
        # Remove trending status
        not_trending = self.model.objects.filter(
            is_deleted=False
        ).exclude(
            post_count__gte=min_posts,
            last_used__gte=recent_date
        )
        not_trending.update(is_trending=False)


class PostService(PublishableService, ViewTrackingService, SearchService):
    """Service for managing posts with full functionality."""
    
    model = Post
    
    def __init__(self, user: Optional[User] = None):
        super().__init__(user)
        ViewTrackingService.__init__(self, self.model, user)
        SearchService.__init__(self, self.model, user)
    
    def get_queryset(self):
        """Get posts with optimized queries."""
        return self.model.objects.filter(is_deleted=False).select_related(
            'author', 'type', 'organization', 'subsidiary'
        ).prefetch_related(
            'categories', 'subcategories', 'hashtags', 'attachments'
        )
    
    @transaction.atomic
    def create_post(self, data: Dict[str, Any]) -> Post:
        """Create a new post with all relationships."""
        # Extract relationship data
        categories = data.pop('categories', [])
        subcategories = data.pop('subcategories', [])
        hashtags = data.pop('hashtags', [])
        
        # Validate business rules
        self._validate_post_creation(data)
        
        # Set current user for audit
        if self.user:
            data['author'] = self.user
        
        # Create the post
        post = self.create(data)
        post._current_user = self.user
        
        # Add relationships
        self._add_post_relationships(post, categories, subcategories, hashtags)
        
        return post
    
    @transaction.atomic
    def update_post(self, post_id: Any, data: Dict[str, Any]) -> Post:
        """Update an existing post with all relationships."""
        post = self.get_by_id(post_id)
        
        # Check permissions
        if not self._can_edit_post(post):
            raise PermissionDeniedError("You don't have permission to edit this post")
        
        # Extract relationship data
        categories = data.pop('categories', None)
        subcategories = data.pop('subcategories', None)
        hashtags = data.pop('hashtags', None)
        
        # Update the post
        post = self.update(post_id, data)
        post._current_user = self.user
        
        # Update relationships if provided
        if categories is not None:
            self._update_post_categories(post, categories)
        if subcategories is not None:
            self._update_post_subcategories(post, subcategories)
        if hashtags is not None:
            self._update_post_hashtags(post, hashtags)
        
        return post
    
    def get_published_posts(self, filters: Dict[str, Any] = None, limit: int = 20) -> List[Post]:
        """Get published posts with filters."""
        base_filters = {'status': 'published'}
        if filters:
            base_filters.update(filters)
        
        return self.list(base_filters, ['-priority', '-published_at'])[:limit]
    
    def get_featured_posts(self, limit: int = 5) -> List[Post]:
        """Get featured posts."""
        return self.get_published_posts({'is_featured': True}, limit)
    
    def get_urgent_posts(self, limit: int = 10) -> List[Post]:
        """Get urgent posts."""
        return self.get_published_posts({'is_urgent': True}, limit)
    
    def get_posts_by_organization(self, organization_id: Any, limit: int = 20) -> List[Post]:
        """Get posts by organization."""
        return self.get_published_posts({'organization_id': organization_id}, limit)
    
    def get_posts_by_type(self, post_type_id: Any, limit: int = 20) -> List[Post]:
        """Get posts by type."""
        return self.get_published_posts({'type_id': post_type_id}, limit)
    
    def get_posts_by_category(self, category_id: Any, limit: int = 20) -> List[Post]:
        """Get posts by category."""
        posts = self.get_queryset().filter(
            categories__id=category_id,
            status='published'
        ).order_by('-priority', '-published_at')[:limit]
        
        return list(posts)
    
    def get_posts_by_hashtag(self, hashtag_id: Any, limit: int = 20) -> List[Post]:
        """Get posts by hashtag."""
        posts = self.get_queryset().filter(
            hashtags__id=hashtag_id,
            status='published'
        ).order_by('-priority', '-published_at')[:limit]
        
        return list(posts)
    
    def search_posts(self, query: str, filters: Dict[str, Any] = None, limit: int = 20) -> List[Post]:
        """Search posts by title and content."""
        queryset = self.get_queryset().filter(status='published')
        
        if filters:
            queryset = queryset.filter(**filters)
        
        if query:
            search_query = Q(title__icontains=query) | Q(content__icontains=query) | \
                          Q(title_ar__icontains=query) | Q(content_ar__icontains=query) | \
                          Q(summary__icontains=query) | Q(summary_ar__icontains=query)
            queryset = queryset.filter(search_query)
        
        return list(queryset.order_by('-priority', '-published_at')[:limit])
    
    def get_user_posts(self, user_id: Any, status: str = None) -> List[Post]:
        """Get posts by user."""
        filters = {'author_id': user_id}
        if status:
            filters['status'] = status
        
        return self.list(filters, ['-created_at'])
    
    def _validate_post_creation(self, data: Dict[str, Any]) -> None:
        """Validate post creation data."""
        # Check if organization exists and user has permission
        if 'organization' in data:
            org = data['organization']
            if not self._can_post_to_organization(org):
                raise PermissionDeniedError("You don't have permission to post to this organization")
        
        # Validate subsidiary belongs to organization
        if 'subsidiary' in data and 'organization' in data:
            subsidiary = data['subsidiary']
            organization = data['organization']
            if subsidiary and subsidiary.organization != organization:
                raise BusinessLogicError("Subsidiary must belong to the selected organization")
    
    def _can_edit_post(self, post: Post) -> bool:
        """Check if user can edit the post."""
        if not self.user:
            return False
        
        # Superuser or author can edit
        if self.user.is_superuser or post.author == self.user:
            return True
        
        # Organization admin can edit posts in their organization
        if hasattr(self.user, 'organization_memberships'):
            return self.user.organization_memberships.filter(
                organization=post.organization,
                role__in=['admin', 'editor']
            ).exists()
        
        return False
    
    def _can_post_to_organization(self, organization: Organization) -> bool:
        """Check if user can post to the organization."""
        if not self.user:
            return False
        
        if self.user.is_superuser:
            return True
        
        # Check organization membership
        if hasattr(self.user, 'organization_memberships'):
            return self.user.organization_memberships.filter(
                organization=organization,
                role__in=['admin', 'editor', 'author']
            ).exists()
        
        return False
    
    def _add_post_relationships(self, post: Post, categories: List[Any], 
                              subcategories: List[Any], hashtags: List[str]) -> None:
        """Add relationships to a post."""
        if categories:
            self._update_post_categories(post, categories)
        
        if subcategories:
            self._update_post_subcategories(post, subcategories)
        
        if hashtags:
            self._update_post_hashtags(post, hashtags)
    
    def _update_post_categories(self, post: Post, category_ids: List[Any]) -> None:
        """Update post categories."""
        # Remove existing relationships
        PostCategory.objects.filter(post=post).delete()
        
        # Add new relationships
        for category_id in category_ids:
            try:
                category = Category.objects.get(id=category_id, is_deleted=False, is_active=True)
                PostCategory.objects.create(post=post, category=category)
                category.update_post_count()
            except Category.DoesNotExist:
                continue
    
    def _update_post_subcategories(self, post: Post, subcategory_ids: List[Any]) -> None:
        """Update post subcategories."""
        # Remove existing relationships
        PostSubCategory.objects.filter(post=post).delete()
        
        # Add new relationships
        for subcategory_id in subcategory_ids:
            try:
                subcategory = SubCategory.objects.get(id=subcategory_id, is_deleted=False, is_active=True)
                PostSubCategory.objects.create(post=post, subcategory=subcategory)
                subcategory.update_post_count()
            except SubCategory.DoesNotExist:
                continue
    
    def _update_post_hashtags(self, post: Post, hashtag_names: List[str]) -> None:
        """Update post hashtags."""
        # Remove existing relationships
        PostHashTag.objects.filter(post=post).delete()
        
        # Add new relationships
        for hashtag_name in hashtag_names:
            hashtag, created = HashTag.objects.get_or_create(
                name=hashtag_name.lower().strip(),
                defaults={'is_active': True}
            )
            PostHashTag.objects.create(post=post, hashtag=hashtag)
            hashtag.update_post_count()


class PostAttachmentService(CRUDService):
    """Service for managing post attachments."""
    
    model = PostAttachment
    
    def get_queryset(self):
        """Get attachments with post information."""
        return self.model.objects.filter(is_deleted=False).select_related('post')
    
    def get_post_attachments(self, post_id: Any) -> List[PostAttachment]:
        """Get all attachments for a post."""
        return self.list({'post_id': post_id}, ['order', 'created_at'])
    
    def get_public_attachments(self, post_id: Any) -> List[PostAttachment]:
        """Get public attachments for a post."""
        return self.list({'post_id': post_id, 'is_public': True}, ['order', 'created_at'])
    
    @transaction.atomic
    def add_attachment(self, post_id: Any, file_data: Dict[str, Any]) -> PostAttachment:
        """Add an attachment to a post."""
        # Get the post
        post = Post.objects.get(id=post_id, is_deleted=False)
        
        # Check permissions
        if not self._can_add_attachment_to_post(post):
            raise PermissionDeniedError("You don't have permission to add attachments to this post")
        
        # Set the post
        file_data['post'] = post
        
        # Set order if not provided
        if 'order' not in file_data:
            max_order = PostAttachment.objects.filter(post=post).aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            file_data['order'] = max_order + 1
        
        return self.create(file_data)
    
    def track_download(self, attachment_id: Any) -> None:
        """Track attachment download."""
        try:
            attachment = self.get_by_id(attachment_id)
            attachment.increment_download_count()
            
            self._log_action('download', attachment_id, {
                'post_id': attachment.post.id,
                'file_name': attachment.file.name
            })
        except NotFoundError:
            pass
    
    def _can_add_attachment_to_post(self, post: Post) -> bool:
        """Check if user can add attachments to the post."""
        if not self.user:
            return False
        
        if self.user.is_superuser or post.author == self.user:
            return True
        
        # Organization admin can add attachments
        if hasattr(self.user, 'organization_memberships'):
            return self.user.organization_memberships.filter(
                organization=post.organization,
                role__in=['admin', 'editor']
            ).exists()
        
        return False