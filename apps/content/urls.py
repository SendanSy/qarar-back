from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    HashTagViewSet,
    BookmarkViewSet,
    PostTypeViewSet,
    PostViewSet,
    SearchViewSet,
    HealthCheckViewSet
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'hashtags', HashTagViewSet)
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'post-types', PostTypeViewSet)
router.register(r'posts', PostViewSet)
router.register(r'search', SearchViewSet, basename='search')
router.register(r'health', HealthCheckViewSet, basename='health')

# URL patterns
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
] 