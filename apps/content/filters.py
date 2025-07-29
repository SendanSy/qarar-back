"""
Filters for content models.
"""
from django_filters import rest_framework as filters
from django.db.models import Q
from .models.post import Post
from .models.classification import Category


class PostFilter(filters.FilterSet):
    """
    Advanced filtering for posts with optimized querysets.
    """
    # Date filters
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    published_after = filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    
    # Content filters
    category = filters.CharFilter(field_name='categories__slug', lookup_expr='exact')
    category_id = filters.UUIDFilter(field_name='categories__id')
    subcategory = filters.CharFilter(field_name='subcategories__slug', lookup_expr='exact')
    subcategory_id = filters.UUIDFilter(field_name='subcategories__id')
    hashtag = filters.CharFilter(field_name='hashtags__name', lookup_expr='icontains')
    
    # Performance filters
    min_views = filters.NumberFilter(field_name='view_count', lookup_expr='gte')
    max_views = filters.NumberFilter(field_name='view_count', lookup_expr='lte')
    min_reading_time = filters.NumberFilter(field_name='reading_time', lookup_expr='gte')
    max_reading_time = filters.NumberFilter(field_name='reading_time', lookup_expr='lte')
    
    # Language filter
    language = filters.CharFilter(field_name='language_code')
    
    # Custom search filter (note: DRF's SearchFilter handles 'search' parameter)
    content_search = filters.CharFilter(method='filter_search')
    
    # Organization filters
    organization_code = filters.CharFilter(field_name='organization__code')
    subsidiary_code = filters.CharFilter(field_name='subsidiary__code')
    department = filters.NumberFilter(field_name='department__id')
    department_code = filters.CharFilter(field_name='department__code')
    
    class Meta:
        model = Post
        fields = {
            'status': ['exact', 'in'],
            'author': ['exact'],
            'type': ['exact'],
            'organization': ['exact'],
            'subsidiary': ['exact'],
            'department': ['exact'],
        }
    
    def filter_search(self, queryset, name, value):
        """
        Custom content search filter that searches across multiple fields.
        This is different from DRF's SearchFilter which uses the 'search' parameter.
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(title_ar__icontains=value) |
            Q(content__icontains=value) |
            Q(content_ar__icontains=value) |
            Q(summary__icontains=value) |
            Q(summary_ar__icontains=value) |
            Q(meta_keywords__icontains=value) |
            Q(author__username__icontains=value) |
            Q(author__first_name__icontains=value) |
            Q(author__last_name__icontains=value)
        )


class CategoryFilter(filters.FilterSet):
    """
    Filtering for categories.
    """
    name = filters.CharFilter(lookup_expr='icontains')
    name_ar = filters.CharFilter(lookup_expr='icontains')
    has_posts = filters.BooleanFilter(method='filter_has_posts')
    min_post_count = filters.NumberFilter(method='filter_min_post_count')
    
    class Meta:
        model = Category
        fields = {
            'is_active': ['exact'],
        }
    
    def filter_has_posts(self, queryset, name, value):
        """Filter categories that have posts."""
        if value:
            return queryset.filter(posts__isnull=False).distinct()
        return queryset.filter(posts__isnull=True)
    
    def filter_min_post_count(self, queryset, name, value):
        """Filter categories with minimum post count."""
        from django.db.models import Count
        return queryset.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).filter(post_count__gte=value)