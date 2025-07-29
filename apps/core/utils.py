"""
Utility functions for the core app
"""
from django.conf import settings
from django.utils.translation import gettext_lazy as _


def environment_callback(request):
    """
    Callback to display current environment in admin
    """
    env = settings.DEBUG and "development" or "production"
    color = {
        "development": "green",
        "staging": "yellow",
        "production": "red"
    }.get(env, "gray")
    
    return {
        "name": env.upper(),
        "color": color,
    }


def post_count_callback(request):
    """
    Callback to display post count in sidebar
    """
    from apps.content.models import Post
    count = Post.objects.filter(status='published', is_deleted=False).count()
    
    if count > 99:
        return "99+"
    elif count > 0:
        return str(count)
    return None