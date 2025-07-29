"""
Admin configuration for users app with Django Unfold
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RangeDateFilter
from .models import User, UserInterest, UserFollowing


class UserInterestInline(TabularInline):
    """Inline for user interests"""
    model = UserInterest
    extra = 0
    autocomplete_fields = ['category']


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Admin configuration for User model"""
    
    list_display = [
        'username',
        'email',
        'full_name_display',
        'user_type_display',
        'is_active_display',
        'is_verified_display',
        'date_joined',
        'last_login',
    ]
    
    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'user_type',
        'is_verified',
        ('date_joined', RangeDateFilter),
        ('last_login', RangeDateFilter),
    ]
    
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (_('Authentication'), {
            'fields': ('username', 'password')
        }),
        (_('Personal Information'), {
            'fields': (
                ('first_name', 'last_name'),
                'email',
                'bio',
                ('profile_picture', 'cover_photo'),
                ('website', 'location'),
            )
        }),
        (_('Social Media'), {
            'fields': (
                ('twitter', 'facebook'),
                ('instagram', 'linkedin'),
            ),
            'classes': ('collapse',),
        }),
        (_('Status & Permissions'), {
            'fields': (
                'user_type',
                'is_verified',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'user_type',
                'is_active',
                'is_staff',
            ),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']
    inlines = [UserInterestInline]
    
    @display(description=_('Full Name'))
    def full_name_display(self, obj):
        full_name = obj.get_full_name()
        if full_name:
            return full_name
        return '-'
    
    @display(description=_('Type'), ordering='user_type')
    def user_type_display(self, obj):
        colors = {
            'admin': '#ef4444',
            'editor': '#3b82f6',
            'viewer': '#10b981',
            'contributor': '#f59e0b',
        }
        labels = {
            'admin': _('Admin'),
            'editor': _('Editor'),
            'viewer': _('Viewer'),
            'contributor': _('Contributor'),
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.user_type, '#666'),
            labels.get(obj.user_type, obj.user_type)
        )
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    @display(description=_('Verified'), boolean=True)
    def is_verified_display(self, obj):
        return obj.is_verified
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('groups', 'user_permissions')


@admin.register(UserFollowing)
class UserFollowingAdmin(ModelAdmin):
    """Admin configuration for UserFollowing model"""
    
    list_display = ['user', 'following_user', 'created_at']
    list_filter = [('created_at', RangeDateFilter)]
    search_fields = ['user__username', 'user__email', 'following_user__username', 'following_user__email']
    autocomplete_fields = ['user', 'following_user']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Following Relationship'), {
            'fields': (
                'user',
                'following_user',
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at']


# Unregister and re-register Group with Unfold
admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(ModelAdmin):
    """Admin configuration for Group model with Unfold"""
    list_display = ['name', 'permissions_count']
    search_fields = ['name']
    filter_horizontal = ['permissions']
    
    @display(description=_('Permissions'))
    def permissions_count(self, obj):
        count = obj.permissions.count()
        return format_html(
            '<span style="background: #3b82f6; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )