"""
Core admin dashboard and utilities
"""
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from datetime import datetime, timedelta


def dashboard_callback(request, context):
    """
    Custom dashboard callback for Django Unfold
    Provides statistics and metrics for the admin dashboard
    """
    from apps.content.models import Post, Category, HashTag
    from apps.producers.models import Organization
    from apps.users.models import User
    
    # Get date ranges
    today = datetime.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Post statistics
    total_posts = Post.objects.filter(is_deleted=False).count()
    published_posts = Post.objects.filter(status='published', is_deleted=False).count()
    draft_posts = Post.objects.filter(status='draft', is_deleted=False).count()
    recent_posts = Post.objects.filter(created_at__gte=last_week, is_deleted=False).count()
    
    # User statistics
    total_users = User.objects.filter(is_active=True).count()
    verified_users = User.objects.filter(is_verified=True, is_active=True).count()
    recent_users = User.objects.filter(date_joined__gte=last_month).count()
    
    # Organization statistics
    total_organizations = Organization.objects.filter(is_deleted=False).count()
    verified_organizations = Organization.objects.filter(is_verified=True, is_deleted=False).count()
    
    # Category and hashtag statistics
    active_categories = Category.objects.filter(is_active=True, is_deleted=False).count()
    trending_hashtags = HashTag.objects.filter(is_trending=True, is_deleted=False).count()
    
    # Top content
    popular_posts = Post.objects.filter(
        status='published',
        is_deleted=False
    ).order_by('-view_count')[:5]
    
    recent_posts_list = Post.objects.filter(
        is_deleted=False
    ).order_by('-created_at')[:5]
    
    # Dashboard sections
    context.update({
        "custom_cards": [
            {
                "title": _("Content Overview"),
                "metrics": [
                    {
                        "title": _("Total Posts"),
                        "value": total_posts,
                        "footer": f"{recent_posts} " + str(_("new this week")),
                    },
                    {
                        "title": _("Published"),
                        "value": published_posts,
                        "color": "green",
                    },
                    {
                        "title": _("Drafts"),
                        "value": draft_posts,
                        "color": "yellow",
                    },
                ],
            },
            {
                "title": _("Users & Organizations"),
                "metrics": [
                    {
                        "title": _("Active Users"),
                        "value": total_users,
                        "footer": f"{verified_users} " + str(_("verified")),
                    },
                    {
                        "title": _("Organizations"),
                        "value": total_organizations,
                        "footer": f"{verified_organizations} " + str(_("verified")),
                    },
                    {
                        "title": _("New Users"),
                        "value": recent_users,
                        "footer": _("Last 30 days"),
                    },
                ],
            },
            {
                "title": _("Classification"),
                "metrics": [
                    {
                        "title": _("Categories"),
                        "value": active_categories,
                        "color": "blue",
                    },
                    {
                        "title": _("Trending Hashtags"),
                        "value": trending_hashtags,
                        "color": "purple",
                    },
                ],
            },
        ],
        "popular_posts": popular_posts,
        "recent_posts": recent_posts_list,
    })
    
    return context