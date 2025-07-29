"""
Core admin dashboard and utilities
"""
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json
from django.core.serializers.json import DjangoJSONEncoder


def dashboard_callback(request, context):
    """
    Custom dashboard callback for Django Unfold
    Provides statistics and metrics for the admin dashboard
    """
    from apps.content.models import Post, Category, HashTag, PostType
    from apps.producers.models import Organization, Subsidiary
    from apps.users.models import User
    from apps.geographics.models import Country, State, City
    
    # Get date ranges
    now = timezone.now()
    today = now.date()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    last_90_days = today - timedelta(days=90)
    
    # Post statistics
    total_posts = Post.objects.filter(is_deleted=False).count()
    published_posts = Post.objects.filter(status='published', is_deleted=False).count()
    draft_posts = Post.objects.filter(status='draft', is_deleted=False).count()
    archived_posts = Post.objects.filter(status='archived', is_deleted=False).count()
    
    # Recent post activity
    posts_last_7_days = Post.objects.filter(
        created_at__gte=last_7_days,
        is_deleted=False
    ).count()
    posts_last_30_days = Post.objects.filter(
        created_at__gte=last_30_days,
        is_deleted=False
    ).count()
    
    # User statistics
    total_users = User.objects.filter(is_active=True).count()
    verified_users = User.objects.filter(is_verified=True, is_active=True).count()
    staff_users = User.objects.filter(is_staff=True, is_active=True).count()
    new_users_last_30_days = User.objects.filter(date_joined__gte=last_30_days).count()
    
    # Organization statistics
    total_organizations = Organization.objects.count()
    verified_organizations = Organization.objects.filter(is_verified=True).count()
    total_subsidiaries = Subsidiary.objects.filter(is_active=True).count()
    
    # Geographic data statistics
    total_countries = Country.objects.filter(is_active=True).count()
    total_states = State.objects.filter(is_active=True).count()
    total_cities = City.objects.filter(is_active=True).count()
    
    # Content classification statistics
    active_categories = Category.objects.filter(is_active=True, is_deleted=False).count()
    total_hashtags = HashTag.objects.filter(is_deleted=False).count()
    trending_hashtags = HashTag.objects.filter(is_trending=True, is_deleted=False).count()
    post_types_count = PostType.objects.filter(is_active=True).count()
    
    # Calculate engagement metrics
    total_views = Post.objects.filter(is_deleted=False).aggregate(
        total=Sum('view_count')
    )['total'] or 0
    
    avg_views_per_post = Post.objects.filter(
        status='published',
        is_deleted=False
    ).aggregate(avg=Avg('view_count'))['avg'] or 0
    
    # Posts by type
    posts_by_type = list(PostType.objects.filter(is_active=True).annotate(
        total_posts=Count('posts', filter=Q(posts__is_deleted=False))
    ).values('name', 'total_posts').order_by('-total_posts')[:5])
    
    # Posts by category
    posts_by_category = list(Category.objects.filter(
        is_active=True,
        is_deleted=False
    ).annotate(
        total_posts=Count('posts', filter=Q(posts__is_deleted=False))
    ).values('name', 'total_posts').order_by('-total_posts')[:5])
    
    # Recent posts for activity feed
    recent_posts = Post.objects.filter(
        is_deleted=False
    ).select_related('author', 'organization', 'type').order_by('-created_at')[:10]
    
    # Most viewed posts
    popular_posts = Post.objects.filter(
        status='published',
        is_deleted=False
    ).order_by('-view_count')[:5]
    
    # Posts trend data (last 30 days)
    posts_trend = []
    for i in range(30):
        date = today - timedelta(days=i)
        count = Post.objects.filter(
            created_at__date=date,
            is_deleted=False
        ).count()
        posts_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    posts_trend.reverse()
    
    # User registration trend (last 30 days)
    users_trend = []
    for i in range(30):
        date = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=date).count()
        users_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    users_trend.reverse()
    
    # Top contributing organizations
    top_organizations = list(Organization.objects.annotate(
        total_posts=Count('posts', filter=Q(posts__is_deleted=False))
    ).order_by('-total_posts')[:5].values('name', 'total_posts'))
    
    # Calculate growth percentages
    def calculate_growth(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    posts_prev_7_days = Post.objects.filter(
        created_at__date__range=[last_7_days - timedelta(days=7), last_7_days],
        is_deleted=False
    ).count()
    posts_growth = calculate_growth(posts_last_7_days, posts_prev_7_days)
    
    # Update context with dashboard data
    context.update({
        # Summary cards
        'summary_cards': [
            {
                'title': _('Total Posts'),
                'value': f'{total_posts:,}',
                'subtitle': f'{posts_last_7_days} new this week',
                'color': 'primary',
                'icon': 'article',
                'change': f'{posts_growth:+.1f}%' if posts_growth else '0%',
                'change_type': 'increase' if posts_growth > 0 else 'decrease' if posts_growth < 0 else 'neutral'
            },
            {
                'title': _('Active Users'),
                'value': f'{total_users:,}',
                'subtitle': f'{verified_users} verified',
                'color': 'success',
                'icon': 'people',
                'detail': f'{new_users_last_30_days} new in 30 days'
            },
            {
                'title': _('Organizations'),
                'value': f'{total_organizations:,}',
                'subtitle': f'{verified_organizations} verified',
                'color': 'info',
                'icon': 'business',
                'detail': f'{total_subsidiaries} subsidiaries'
            },
            {
                'title': _('Total Views'),
                'value': f'{total_views:,}',
                'subtitle': f'Avg {avg_views_per_post:.0f} per post',
                'color': 'warning',
                'icon': 'visibility',
            },
        ],
        
        # Status breakdown
        'post_status_data': {
            'labels': json.dumps(['Published', 'Draft', 'Archived'], cls=DjangoJSONEncoder),
            'data': json.dumps([published_posts, draft_posts, archived_posts], cls=DjangoJSONEncoder),
            'colors': json.dumps(['#22c55e', '#f59e0b', '#6b7280'], cls=DjangoJSONEncoder)
        },
        
        # Geographic distribution
        'geographic_stats': {
            'countries': total_countries,
            'states': total_states,
            'cities': total_cities,
        },
        
        # Content classification
        'content_stats': {
            'categories': active_categories,
            'hashtags': total_hashtags,
            'trending': trending_hashtags,
            'post_types': post_types_count,
        },
        
        # Charts data (JSON serialized for template)
        'posts_by_type_chart': {
            'labels': json.dumps([item['name'] for item in posts_by_type], cls=DjangoJSONEncoder),
            'data': json.dumps([item['total_posts'] for item in posts_by_type], cls=DjangoJSONEncoder),
        },
        
        'posts_by_category_chart': {
            'labels': json.dumps([item['name'] for item in posts_by_category], cls=DjangoJSONEncoder),
            'data': json.dumps([item['total_posts'] for item in posts_by_category], cls=DjangoJSONEncoder),
        },
        
        'posts_trend_chart': {
            'labels': json.dumps([item['date'] for item in posts_trend], cls=DjangoJSONEncoder),
            'data': json.dumps([item['count'] for item in posts_trend], cls=DjangoJSONEncoder),
        },
        
        'users_trend_chart': {
            'labels': json.dumps([item['date'] for item in users_trend], cls=DjangoJSONEncoder),
            'data': json.dumps([item['count'] for item in users_trend], cls=DjangoJSONEncoder),
        },
        
        # Lists
        'recent_posts': recent_posts,
        'popular_posts': popular_posts,
        'top_organizations': top_organizations,
        
        # Additional metrics
        'quick_stats': [
            {'label': _('Posts Today'), 'value': Post.objects.filter(created_at__date=today, is_deleted=False).count()},
            {'label': _('Active Categories'), 'value': active_categories},
            {'label': _('Staff Users'), 'value': staff_users},
            {'label': _('Trending Tags'), 'value': trending_hashtags},
        ],
    })
    
    return context