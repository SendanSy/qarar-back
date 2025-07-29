from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    UserViewSet,
    UserInterestViewSet,
    UserRegistrationView,
    UserSearchView,
    CustomTokenObtainPairView,
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'interests', UserInterestViewSet, basename='interest')

# URL patterns
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Authentication URLs
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    
    # Search URLs
    path('search/', UserSearchView.as_view(), name='user-search'),
    
    # User profile endpoints
    path('me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    path('me/update/', UserViewSet.as_view({'put': 'update_me', 'patch': 'update_me'}), name='user-update-me'),
    path('me/change-password/', UserViewSet.as_view({'post': 'change_password'}), name='user-change-password'),
] 