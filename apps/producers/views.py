"""
API views for producers app
"""
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Prefetch
from django_filters.rest_framework import DjangoFilterBackend

from .models import Organization, Subsidiary, Department
from .serializers import (
    OrganizationSerializer, SubsidiarySerializer, DepartmentSerializer,
    OrganizationDetailSerializer, OrganizationListSerializer
)
from .filters import OrganizationFilter, SubsidiaryFilter, DepartmentFilter


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for organizations - public read-only access
    """
    queryset = Organization.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrganizationFilter
    search_fields = ['name', 'name_ar', 'code', 'description', 'description_ar']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    lookup_field = 'code'
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'retrieve':
            return OrganizationDetailSerializer
        return OrganizationListSerializer
    
    def get_queryset(self):
        """Optimize queryset based on action"""
        queryset = super().get_queryset()
        
        if self.action == 'list':
            # For list view, annotate with counts
            queryset = queryset.annotate(
                active_subsidiary_count=Count(
                    'subsidiaries',
                    filter=Q(subsidiaries__is_active=True)
                ),
                active_department_count=Count(
                    'subsidiaries__departments',
                    filter=Q(
                        subsidiaries__is_active=True,
                        subsidiaries__departments__is_active=True
                    )
                )
            ).select_related('country', 'state', 'city')
        
        elif self.action == 'retrieve':
            # For detail view, prefetch related data
            queryset = queryset.prefetch_related(
                Prefetch(
                    'subsidiaries',
                    queryset=Subsidiary.objects.filter(is_active=True).prefetch_related(
                        Prefetch(
                            'departments',
                            queryset=Department.objects.filter(is_active=True)
                        )
                    )
                )
            ).select_related('country', 'state', 'city')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def posts(self, request, code=None):
        """Get all posts for an organization including subsidiaries and departments"""
        organization = self.get_object()
        
        # Get posts directly from organization
        from apps.content.models.post import Post
        from apps.content.serializers import PostSerializer
        
        posts = Post.objects.filter(
            Q(organization=organization) |
            Q(subsidiary__parent_organization=organization) |
            Q(department__subsidiary__parent_organization=organization),
            status='published'
        ).distinct().select_related(
            'author', 'type', 'organization', 'subsidiary', 'department'
        ).prefetch_related('categories', 'hashtags')
        
        # Apply pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subsidiaries(self, request, code=None):
        """Get subsidiaries for an organization"""
        organization = self.get_object()
        subsidiaries = organization.subsidiaries.filter(is_active=True)
        serializer = SubsidiarySerializer(subsidiaries, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def departments(self, request, code=None):
        """Get all departments under an organization"""
        organization = self.get_object()
        departments = Department.objects.filter(
            subsidiary__parent_organization=organization,
            is_active=True
        ).select_related('subsidiary')
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)


class SubsidiaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subsidiaries - public read-only access
    """
    queryset = Subsidiary.objects.filter(is_active=True)
    serializer_class = SubsidiarySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubsidiaryFilter
    search_fields = ['name', 'name_ar', 'code', 'description', 'description_ar']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    lookup_field = 'code'
    
    def get_queryset(self):
        """Optimize queryset"""
        return super().get_queryset().select_related(
            'parent_organization', 'country', 'state', 'city'
        ).prefetch_related('departments')
    
    @action(detail=True, methods=['get'])
    def departments(self, request, code=None):
        """Get departments for a subsidiary"""
        subsidiary = self.get_object()
        departments = subsidiary.departments.filter(is_active=True)
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, code=None):
        """Get posts for a subsidiary"""
        subsidiary = self.get_object()
        
        from apps.content.models.post import Post
        from apps.content.serializers import PostSerializer
        
        posts = Post.objects.filter(
            Q(subsidiary=subsidiary) |
            Q(department__subsidiary=subsidiary),
            status='published'
        ).distinct().select_related(
            'author', 'type', 'organization', 'subsidiary', 'department'
        ).prefetch_related('categories', 'hashtags')
        
        # Apply pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for departments - public read-only access
    """
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DepartmentFilter
    search_fields = ['name', 'name_ar', 'code', 'description', 'description_ar', 'head_name']
    ordering_fields = ['name', 'created_at', 'employee_count']
    ordering = ['name']
    lookup_field = 'code'
    
    def get_queryset(self):
        """Optimize queryset"""
        return super().get_queryset().select_related(
            'subsidiary', 'subsidiary__parent_organization'
        )
    
    @action(detail=True, methods=['get'])
    def posts(self, request, code=None):
        """Get posts for a department"""
        department = self.get_object()
        
        from apps.content.models.post import Post
        from apps.content.serializers import PostSerializer
        
        posts = Post.objects.filter(
            department=department,
            status='published'
        ).select_related(
            'author', 'type', 'organization', 'subsidiary', 'department'
        ).prefetch_related('categories', 'hashtags')
        
        # Apply pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)