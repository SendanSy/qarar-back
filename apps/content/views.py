"""
API views with caching, monitoring, and performance improvements.
"""
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db.models import Q, Prefetch, F
from django.utils import timezone

from apps.core.permissions import IsOwnerOrReadOnly
from .models.post import Post, PostType, PostAttachment
from .models.classification import Category, SubCategory, HashTag
from .models.bookmark import Bookmark
from .serializers import (
    PostSerializer, CategorySerializer, HashTagSerializer,
    PostTypeSerializer, BookmarkSerializer
)
from .filters import PostFilter, CategoryFilter


class PostViewSet(viewsets.ModelViewSet):
    """
    Post ViewSet with caching and performance monitoring.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filterset_class = PostFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'title_ar', 'content', 'content_ar']
    ordering_fields = ['created_at', 'published_at', 'view_count']
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get optimized queryset based on action."""
        if self.action == 'list':
            queryset = Post.objects.select_related(
                'author', 'type', 'organization', 'subsidiary'
            ).prefetch_related(
                'categories', 'subcategories', 'hashtags'
            )
        elif self.action == 'retrieve':
            queryset = Post.objects.select_related(
                'author', 'type', 'organization', 'subsidiary'
            ).prefetch_related(
                'categories', 'subcategories', 'hashtags', 'attachments'
            )
        else:
            queryset = Post.objects.select_related('author', 'organization')
        
        # Filter based on user permissions
        user = self.request.user
        if not user.is_authenticated or not user.is_staff:
            queryset = queryset.filter(status='published')
        
        return queryset
    
    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List posts with caching and performance monitoring."""
        # Generate cache key based on filters and pagination
        cache_key = f"post_list_{hash(str(request.GET.dict()))}_{request.GET.get('page', 1)}"
        
        # Try to get from cache
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)
        
        # Get queryset with user context
        queryset = self.filter_queryset(self.get_queryset())
        
        # Add bookmark status for authenticated users
        if request.user.is_authenticated:
            user_bookmarks = Bookmark.objects.filter(
                user=request.user
            ).values_list('post_id', flat=True)
            for post in queryset:
                post.is_bookmarked = post.id in user_bookmarks
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            
            # Cache the response for 5 minutes
            cache.set(cache_key, response_data, 300)
            
            return Response(response_data)
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        
        # Cache the response
        cache.set(cache_key, response_data, 300)
        
        return Response(response_data)
    
    def retrieve(self, request, slug=None):
        """Retrieve post with view tracking and real-time bookmark status."""
        # Get post with optimizations - NO CACHING to ensure bookmark status accuracy
        try:
            post = self.get_queryset().get(slug=slug)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Track view
        Post.objects.filter(id=post.id).update(view_count=F('view_count') + 1)
        
        # Serialize with context to get real-time bookmark status
        serializer = self.get_serializer(post, context={'request': request})
        response_data = serializer.data
        
        return Response(response_data)
    
    def perform_create(self, serializer):
        """Create post with proper handling."""
        post = serializer.save(
            author=self.request.user,
            published_at=timezone.now() if serializer.validated_data.get('status') == 'published' else None
        )
        
        # Invalidate related caches
        cache.delete_many([f"post_list_{i}" for i in range(10)])  # Simple cache invalidation
        
    
    def perform_update(self, serializer):
        """Update post with cache invalidation."""
        old_status = self.get_object().status
        new_status = serializer.validated_data.get('status', old_status)
        
        # Set published_at when status changes to published
        if old_status != 'published' and new_status == 'published':
            serializer.save(published_at=timezone.now())
        else:
            serializer.save()
        
        # Invalidate list caches only (post detail is not cached)
        cache.delete_many([f"post_list_{i}" for i in range(10)])
    
    @action(detail=True, methods=['post'])
    def publish(self, request, slug=None):
        """Publish a post."""
        try:
            post = self.get_object()
            if post.status == 'published':
                return Response({'error': 'Post is already published'}, status=status.HTTP_400_BAD_REQUEST)
            
            post.status = 'published'
            post.published_at = timezone.now()
            post.save()
            
            # Invalidate list caches only (post detail is not cached)
            cache.delete_many([f"post_list_{i}" for i in range(10)])
            
            
            serializer = self.get_serializer(post)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def bookmark(self, request, slug=None):
        """Toggle bookmark status for a post."""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            post = self.get_object()
            
            # Check if active bookmark already exists (excluding soft-deleted)
            existing_bookmark = Bookmark.objects.filter(
                user=request.user, 
                post=post,
                is_deleted=False
            ).first()
            
            if existing_bookmark:
                # Bookmark exists, remove it (unbookmark)
                existing_bookmark.delete()  # This does soft delete
                
                return Response({
                    'bookmarked': False,
                    'message': 'Post unbookmarked successfully'
                })
            else:
                # No active bookmark, create new one
                bookmark = Bookmark.objects.create(
                    user=request.user,
                    post=post,
                    notes=request.data.get('notes', '')
                )
                
                # Return bookmark data
                bookmark_data = {
                    'id': str(bookmark.id),
                    'notes': bookmark.notes,
                    'created_at': bookmark.created_at.isoformat()
                }
                
                return Response({
                    'bookmarked': True,
                    'message': 'Post bookmarked successfully',
                    'bookmark': bookmark_data
                })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured posts with caching."""
        cache_key = "featured_posts"
        cached_posts = cache.get(cache_key)
        
        if cached_posts:
            return Response(cached_posts)
        
        queryset = self.get_queryset()[:10]
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        
        cache.set(cache_key, response_data, 1800)  # 30 minutes
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending posts."""
        cache_key = "trending_posts"
        cached_posts = cache.get(cache_key)
        
        if cached_posts:
            return Response(cached_posts)
        
        queryset = self.get_queryset().order_by('-view_count')[:10]
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        
        cache.set(cache_key, response_data, 900)  # 15 minutes
        return Response(response_data)
    


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Category ViewSet with tree structure caching.
    Public access - no authentication required.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    filterset_class = CategoryFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'name_ar']
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get optimized queryset."""
        return Category.objects.filter(is_active=True)
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def list(self, request):
        """List categories with caching."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts for a category."""
        try:
            category = self.get_object()
            posts = Post.objects.filter(
                categories=category,
                status='published'
            ).select_related('author', 'type').prefetch_related('categories')[:20]
            
            category_serializer = self.get_serializer(category)
            posts_serializer = PostSerializer(posts, many=True)
            
            return Response({
                'category': category_serializer.data,
                'posts': posts_serializer.data,
                'total_posts': category.posts.filter(status='published').count()
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HashTagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    HashTag ViewSet with trending support.
    Public access - no authentication required.
    """
    queryset = HashTag.objects.all()
    serializer_class = HashTagSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['post_count', 'last_used']
    ordering = ['-post_count']
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get optimized queryset."""
        return HashTag.objects.all().order_by('-post_count')
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending hashtags."""
        cache_key = "trending_hashtags"
        cached_tags = cache.get(cache_key)
        
        if cached_tags:
            return Response(cached_tags)
        
        hashtags = self.get_queryset()[:20]
        serializer = self.get_serializer(hashtags, many=True)
        response_data = serializer.data
        
        cache.set(cache_key, response_data, 900)  # 15 minutes
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular hashtags."""
        cache_key = "popular_hashtags"
        cached_tags = cache.get(cache_key)
        
        if cached_tags:
            return Response(cached_tags)
        
        hashtags = self.get_queryset()[:30]
        serializer = self.get_serializer(hashtags, many=True)
        response_data = serializer.data
        
        cache.set(cache_key, response_data, 1800)  # 30 minutes
        return Response(response_data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts for a specific hashtag."""
        try:
            hashtag = self.get_object()
            
            # Get query parameters
            limit = int(request.GET.get('limit', 20))
            page = int(request.GET.get('page', 1))
            
            # Get posts for this hashtag
            posts = hashtag.get_posts(status='published', limit=None)
            
            # Paginate manually
            start = (page - 1) * limit
            end = start + limit
            paginated_posts = posts[start:end]
            
            # Serialize data
            hashtag_serializer = self.get_serializer(hashtag)
            posts_serializer = PostSerializer(paginated_posts, many=True, context={'request': request})
            
            return Response({
                'hashtag': hashtag_serializer.data,
                'posts': posts_serializer.data,
                'total_posts': posts.count(),
                'page': page,
                'has_next': end < posts.count(),
                'has_previous': page > 1
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PostTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    PostType ViewSet.
    Public access - no authentication required.
    """
    queryset = PostType.objects.filter(is_active=True)
    serializer_class = PostTypeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'name_ar']
    permission_classes = [permissions.AllowAny]


class BookmarkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for bookmarked content.
    """
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('post')
    
    def perform_create(self, serializer):
        bookmark = serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        # Delete the bookmark
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def posts(self, request):
        """Get all bookmarked posts."""
        bookmarks = self.get_queryset()
        posts = [bookmark.post for bookmark in bookmarks]
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


class SearchViewSet(viewsets.ViewSet):
    """
    Advanced search functionality with caching and analytics.
    Public access - no authentication required.
    """
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        """Unified search across all content types."""
        query = request.GET.get('q', '').strip()
        
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(query) < 2:
            return Response({'error': 'Search query must be at least 2 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get filters
            filters = {
                'category_id': request.GET.get('category'),
                'post_type_id': request.GET.get('type'),
                'organization_id': request.GET.get('organization'),
                'language': request.GET.get('language'),
            }
            
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}
            
            # Perform search using simple queryset filtering for now
            posts = Post.objects.filter(
                Q(title__icontains=query) |
                Q(title_ar__icontains=query) |
                Q(content__icontains=query) |
                Q(content_ar__icontains=query),
                status='published'
            ).select_related('author', 'type').prefetch_related('categories')
            
            # Apply additional filters
            if filters.get('category_id'):
                posts = posts.filter(categories__id=filters['category_id'])
            if filters.get('post_type_id'):
                posts = posts.filter(type__id=filters['post_type_id'])
            
            # Paginate
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', 20))
            start = (page - 1) * per_page
            end = start + per_page
            
            total_results = posts.count()
            posts = posts[start:end]
            
            
            serializer = PostSerializer(posts, many=True)
            return Response({
                'results': serializer.data,
                'total_results': total_results,
                'page': page,
                'per_page': per_page,
                'query': query,
                'filters': filters
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """Get search autocomplete suggestions."""
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return Response([])
        
        try:
            # Simple autocomplete using post titles
            suggestions = Post.objects.filter(
                Q(title__icontains=query) | Q(title_ar__icontains=query),
                status='published'
            ).values_list('title', flat=True)[:10]
            
            return Response(list(suggestions))
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HealthCheckViewSet(viewsets.ViewSet):
    """
    Health check endpoints for monitoring.
    """
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        """Basic health check."""
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })
    
    @action(detail=False, methods=['get'])
    def detailed(self, request):
        """Detailed health check with component status."""
        from apps.core.monitoring import HealthCheckMonitor
        
        health_data = {
            'database': HealthCheckMonitor.check_database(),
            'cache': HealthCheckMonitor.check_cache(),
            'system': HealthCheckMonitor.get_system_metrics()
        }
        
        # Determine overall status
        overall_status = 'healthy'
        for component, status in health_data.items():
            if isinstance(status, dict) and status.get('status') == 'unhealthy':
                overall_status = 'unhealthy'
                break
        
        return Response({
            'status': overall_status,
            'components': health_data,
            'timestamp': timezone.now().isoformat()
        })