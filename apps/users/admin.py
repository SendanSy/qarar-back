from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserInterest, UserFollowing


class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 1


class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'bio', 'profile_picture', 'cover_photo', 'website', 'location')}),
        (_('Social links'), {'fields': ('twitter', 'facebook', 'instagram', 'linkedin')}),
        (_('Status'), {'fields': ('user_type', 'is_verified')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'user_type', 'is_verified')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    inlines = [UserInterestInline]


class UserFollowingAdmin(admin.ModelAdmin):
    list_display = ('user', 'following_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'following_user__username')
    date_hierarchy = 'created_at'


# Register models
admin.site.register(User, UserAdmin)
admin.site.register(UserFollowing, UserFollowingAdmin)
