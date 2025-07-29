from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.db.models import Count
from django.shortcuts import get_object_or_404

from .serializers import (
    UserSerializer, 
    UserDetailSerializer, 
    UserRegistrationSerializer, 
    UserInterestSerializer,
    UserFollowingSerializer,
    UserFollowerSerializer,
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    UserMinimalSerializer
)
from .models import UserInterest, UserFollowing

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses our enhanced token serializer
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    """
    View for user registration with automatic authentication
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """
        Create user and return JWT tokens for immediate authentication
        """
        try:
            # Validate and create user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create the user
            user = serializer.save()
            
            # Generate JWT tokens for immediate authentication
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Prepare comprehensive user data for response
            user_data = UserDetailSerializer(user, context={'request': request}).data
            
            # Return user data with tokens for immediate frontend authentication
            response_data = {
                'user': user_data,
                'access': str(access_token),
                'refresh': str(refresh),
                'message': 'Registration successful. You are now logged in.',
                'token_type': 'Bearer'
            }
            
            headers = self.get_success_headers(serializer.data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            # Handle any unexpected errors during registration
            return Response(
                {'error': 'Registration failed. Please try again.', 'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user operations
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action in ['list', 'search']:
            return UserMinimalSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search users by username or name
        search_term = self.request.query_params.get('search', None)
        if search_term and self.action == 'list':
            queryset = queryset.filter(
                username__icontains=search_term
            ) | queryset.filter(
                first_name__icontains=search_term
            ) | queryset.filter(
                last_name__icontains=search_term
            )
        
        # Filter publishers only
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
            
        # Sort by followers count
        sort_by = self.request.query_params.get('sort_by', None)
        if sort_by == 'followers':
            queryset = queryset.annotate(followers_count=Count('followers')).order_by('-followers_count')
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get the current user's profile
        """
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """
        Update the current user's profile
        """
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """
        Follow a user
        """
        target_user = self.get_object()
        if target_user == request.user:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if already following
        if UserFollowing.objects.filter(user=request.user, following_user=target_user).exists():
            return Response(
                {"detail": "You are already following this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create following relationship
        UserFollowing.objects.create(user=request.user, following_user=target_user)
        return Response({"detail": "You are now following this user."})
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """
        Unfollow a user
        """
        target_user = self.get_object()
        
        # Check if following exists
        following = UserFollowing.objects.filter(user=request.user, following_user=target_user).first()
        if not following:
            return Response(
                {"detail": "You are not following this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Delete following relationship
        following.delete()
        return Response({"detail": "You have unfollowed this user."})
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change user password
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        # Validate input
        if not old_password or not new_password:
            return Response(
                {"detail": "Both old_password and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check old password
        if not user.check_password(old_password):
            return Response(
                {"detail": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({"detail": "Password changed successfully."})
    
    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        """
        Get list of users that this user is following
        """
        user = self.get_object()
        followings = UserFollowing.objects.filter(user=user)
        page = self.paginate_queryset(followings)
        if page is not None:
            serializer = UserFollowingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserFollowingSerializer(followings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """
        Get list of users following this user
        """
        user = self.get_object()
        followers = UserFollowing.objects.filter(following_user=user)
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = UserFollowerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserFollowerSerializer(followers, many=True)
        return Response(serializer.data)


class UserInterestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user interests
    """
    serializer_class = UserInterestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserInterest.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserSearchView(generics.ListAPIView):
    """
    Search for users
    """
    serializer_class = UserMinimalSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        search_term = self.request.query_params.get('q', '')
        if not search_term:
            return User.objects.none()
        
        return User.objects.filter(
            username__icontains=search_term
        ) | User.objects.filter(
            first_name__icontains=search_term
        ) | User.objects.filter(
            last_name__icontains=search_term
        )
