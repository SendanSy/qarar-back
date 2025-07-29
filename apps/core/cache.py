"""
Caching utilities and strategies for the Qarar project.
"""
import hashlib
from typing import Any, Dict, List, Optional, Union
from django.core.cache import cache
from django.conf import settings
from django.db.models import Model
from django.utils import timezone
from functools import wraps
import json
import logging

logger = logging.getLogger(__name__)


class CacheKeyGenerator:
    """
    Utility class for generating consistent cache keys.
    """
    
    @staticmethod
    def make_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.
        """
        # Create a deterministic string from args and kwargs
        key_parts = [str(prefix)]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, Model):
                key_parts.append(f"{arg.__class__.__name__}_{arg.pk}")
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            if isinstance(value, Model):
                key_parts.append(f"{key}_{value.__class__.__name__}_{value.pk}")
            else:
                key_parts.append(f"{key}_{value}")
        
        # Join and hash if too long
        cache_key = ":".join(key_parts)
        
        # Django cache keys have a 250 character limit
        if len(cache_key) > 200:
            hash_part = hashlib.md5(cache_key.encode()).hexdigest()
            cache_key = f"{prefix}:{hash_part}"
        
        return cache_key
    
    @staticmethod
    def model_key(model: Model, action: str = 'detail') -> str:
        """
        Generate a cache key for a model instance.
        """
        return CacheKeyGenerator.make_key(
            f"{model.__class__.__name__.lower()}_{action}",
            model.pk
        )
    
    @staticmethod
    def queryset_key(model_class: type, filters: Dict[str, Any] = None, 
                    ordering: List[str] = None, page: int = None) -> str:
        """
        Generate a cache key for a queryset.
        """
        parts = [f"{model_class.__name__.lower()}_list"]
        
        if filters:
            parts.append(f"filters_{json.dumps(filters, sort_keys=True)}")
        
        if ordering:
            parts.append(f"order_{'_'.join(ordering)}")
        
        if page:
            parts.append(f"page_{page}")
        
        return CacheKeyGenerator.make_key(*parts)


class CacheManager:
    """
    Centralized cache management with invalidation strategies.
    """
    
    # Default cache timeouts (in seconds)
    TIMEOUTS = {
        'short': 300,      # 5 minutes
        'medium': 1800,    # 30 minutes
        'long': 3600,      # 1 hour
        'very_long': 86400, # 24 hours
    }
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get value from cache with logging.
        """
        try:
            value = cache.get(key, default)
            if value is not default:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return default
    
    @classmethod
    def set(cls, key: str, value: Any, timeout: Union[int, str] = 'medium') -> bool:
        """
        Set value in cache with timeout.
        """
        try:
            if isinstance(timeout, str):
                timeout = cls.TIMEOUTS.get(timeout, cls.TIMEOUTS['medium'])
            
            result = cache.set(key, value, timeout)
            logger.debug(f"Cache SET: {key} (timeout: {timeout}s)")
            return result
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """
        Delete key from cache.
        """
        try:
            result = cache.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return result
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False
    
    @classmethod
    def delete_pattern(cls, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        """
        try:
            if hasattr(cache, 'delete_pattern'):
                count = cache.delete_pattern(pattern)
                logger.debug(f"Cache DELETE_PATTERN: {pattern} ({count} keys)")
                return count
            else:
                # Fallback for cache backends that don't support pattern deletion
                logger.warning(f"Cache backend doesn't support pattern deletion: {pattern}")
                return 0
        except Exception as e:
            logger.error(f"Cache DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0
    
    @classmethod
    def invalidate_model(cls, model: Model) -> None:
        """
        Invalidate cache for a specific model instance.
        """
        model_name = model.__class__.__name__.lower()
        patterns = [
            f"{model_name}_detail_{model.pk}*",
            f"{model_name}_list*",
            f"*{model_name}*",
        ]
        
        for pattern in patterns:
            cls.delete_pattern(pattern)
    
    @classmethod
    def invalidate_model_type(cls, model_class: type) -> None:
        """
        Invalidate all cache for a model type.
        """
        model_name = model_class.__name__.lower()
        patterns = [
            f"{model_name}_*",
            f"*{model_name}*",
        ]
        
        for pattern in patterns:
            cls.delete_pattern(pattern)


def cache_result(timeout: Union[int, str] = 'medium', key_prefix: str = None):
    """
    Decorator to cache function results.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = CacheKeyGenerator.make_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = CacheManager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheManager.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


class PostCacheManager:
    """
    Specialized cache manager for post-related operations.
    """
    
    @staticmethod
    def get_post_list_key(filters: Dict[str, Any] = None, page: int = 1) -> str:
        """Generate cache key for post lists."""
        return CacheKeyGenerator.queryset_key(
            model_class=type('Post', (), {}),
            filters=filters,
            page=page
        )
    
    @staticmethod
    def get_post_detail_key(post_id: Any) -> str:
        """Generate cache key for post detail."""
        return CacheKeyGenerator.make_key('post_detail', post_id)
    
    @staticmethod
    def get_post_stats_key(post_id: Any) -> str:
        """Generate cache key for post statistics."""
        return CacheKeyGenerator.make_key('post_stats', post_id)
    
    @staticmethod
    def invalidate_post(post_id: Any) -> None:
        """Invalidate all cache related to a specific post."""
        patterns = [
            f"post_detail_{post_id}*",
            f"post_stats_{post_id}*",
            "post_list*",
            "category_*",
            "hashtag_*",
        ]
        
        for pattern in patterns:
            CacheManager.delete_pattern(pattern)
    
    @staticmethod
    def cache_post_counts() -> Dict[str, int]:
        """Cache and return post counts by status."""
        cache_key = "post_counts_by_status"
        counts = CacheManager.get(cache_key)
        
        if counts is None:
            from apps.content.models.post import Post
            counts = {}
            for status, _ in Post.STATUS_CHOICES:
                counts[status] = Post.objects.filter(
                    status=status, 
                    is_deleted=False
                ).count()
            
            CacheManager.set(cache_key, counts, 'medium')
        
        return counts


class CategoryCacheManager:
    """
    Specialized cache manager for category-related operations.
    """
    
    @staticmethod
    def get_category_tree_key() -> str:
        """Generate cache key for category tree."""
        return "category_tree"
    
    @staticmethod
    def get_category_posts_key(category_id: Any, page: int = 1) -> str:
        """Generate cache key for category posts."""
        return CacheKeyGenerator.make_key('category_posts', category_id, page=page)
    
    @staticmethod
    def invalidate_category(category_id: Any) -> None:
        """Invalidate all cache related to a specific category."""
        patterns = [
            f"category_*{category_id}*",
            "category_tree*",
            "post_list*",
        ]
        
        for pattern in patterns:
            CacheManager.delete_pattern(pattern)
    
    @staticmethod
    def cache_category_tree():
        """Cache the complete category tree with subcategories."""
        cache_key = CategoryCacheManager.get_category_tree_key()
        tree = CacheManager.get(cache_key)
        
        if tree is None:
            from apps.content.models.classification import Category
            
            tree = []
            categories = Category.objects.filter(
                is_deleted=False, 
                is_active=True
            ).prefetch_related('subcategories').order_by('order', 'name')
            
            for category in categories:
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'name_ar': category.name_ar,
                    'slug': category.slug,
                    'icon': category.icon,
                    'post_count': category.post_count,
                    'subcategories': [
                        {
                            'id': sub.id,
                            'name': sub.name,
                            'name_ar': sub.name_ar,
                            'slug': sub.slug,
                            'post_count': sub.post_count,
                        }
                        for sub in category.subcategories.filter(
                            is_deleted=False, 
                            is_active=True
                        ).order_by('order', 'name')
                    ]
                }
                tree.append(category_data)
            
            CacheManager.set(cache_key, tree, 'long')
        
        return tree


# Cache invalidation signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver([post_save, post_delete])
def invalidate_model_cache(sender, instance, **kwargs):
    """
    Signal handler to invalidate cache when models are modified.
    """
    # Only handle our app models
    if not instance._meta.app_label.startswith('apps.'):
        return
    
    try:
        # Invalidate specific model cache
        CacheManager.invalidate_model(instance)
        
        # Special handling for post-related models
        if hasattr(instance, 'post'):
            PostCacheManager.invalidate_post(instance.post.id)
        
        # Special handling for category-related models
        if instance.__class__.__name__ in ['Category', 'SubCategory']:
            CategoryCacheManager.invalidate_category(instance.id)
            CacheManager.delete_pattern("category_tree*")
        
        # Special handling for posts
        if instance.__class__.__name__ == 'Post':
            PostCacheManager.invalidate_post(instance.id)
        
    except Exception as e:
        logger.error(f"Error invalidating cache for {instance}: {e}")


# Utility functions for common caching patterns
def cached_queryset(queryset, cache_key: str, timeout: Union[int, str] = 'medium'):
    """
    Cache a queryset result.
    """
    result = CacheManager.get(cache_key)
    if result is None:
        result = list(queryset)
        CacheManager.set(cache_key, result, timeout)
    return result


def cached_count(queryset, cache_key: str, timeout: Union[int, str] = 'medium'):
    """
    Cache a queryset count.
    """
    count = CacheManager.get(cache_key)
    if count is None:
        count = queryset.count()
        CacheManager.set(cache_key, count, timeout)
    return count