"""
Admin configuration for content app with Django Unfold
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.decorators import action, display
from unfold.contrib.filters.admin import (
    RangeDateFilter, ChoicesDropdownFilter, RelatedDropdownFilter,
    TextFilter
)
from .models import (
    Post, PostType, Category, SubCategory, HashTag,
    PostAttachment, PostCategory, PostSubCategory, PostHashTag,
    Bookmark
)


class PostAttachmentInline(TabularInline):
    """Inline for post attachments"""
    model = PostAttachment
    extra = 0
    fields = ('file', 'title', 'description', 'file_type', 'size', 'order', 'is_public')
    readonly_fields = ('file_type', 'size')
    ordering = ('order',)


class PostCategoryInline(TabularInline):
    """Inline for post categories"""
    model = PostCategory
    extra = 1
    autocomplete_fields = ['category']


class PostSubCategoryInline(TabularInline):
    """Inline for post subcategories"""
    model = PostSubCategory
    extra = 1
    autocomplete_fields = ['subcategory']


class PostHashTagInline(TabularInline):
    """Inline for post hashtags"""
    model = PostHashTag
    extra = 0
    autocomplete_fields = ['hashtag']
    readonly_fields = ('created_at',)


@admin.register(Post)
class PostAdmin(ModelAdmin):
    """Admin configuration for Post model"""
    
    # List display configuration
    list_display = [
        'title_display',
        'post_type_display',
        'organization_display',
        'status_display',
        'view_count',
        'is_featured_display',
        'published_at',
        'created_by',
    ]
    
    list_filter = [
        'status',
        'is_featured',
        'is_pinned',
        ('post_type', RelatedDropdownFilter),
        ('organization', RelatedDropdownFilter),
        ('categories', RelatedDropdownFilter),
        ('published_at', RangeDateFilter),
        ('created_at', RangeDateFilter),
    ]
    
    search_fields = [
        'title', 'title_ar',
        'content', 'content_ar',
        'slug',
        'organization__name', 'organization__name_ar',
    ]
    
    # Form configuration
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('title', 'title_ar'),
                'slug',
                ('post_type', 'priority'),
                ('organization', 'subsidiary'),
            )
        }),
        (_('Content'), {
            'fields': (
                ('summary', 'summary_ar'),
                ('content', 'content_ar'),
            ),
            'classes': ('wide',),
        }),
        (_('Publishing Options'), {
            'fields': (
                'status',
                'published_at',
                ('is_featured', 'is_pinned'),
                'target_audience',
            )
        }),
        (_('SEO Settings'), {
            'fields': (
                ('meta_title', 'meta_title_ar'),
                ('meta_description', 'meta_description_ar'),
                ('meta_keywords', 'meta_keywords_ar'),
            ),
            'classes': ('collapse',),
        }),
        (_('Tracking'), {
            'fields': (
                'view_count',
                ('created_by', 'created_at'),
                ('updated_by', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = [
        'slug', 'view_count', 'created_at', 'updated_at',
        'created_by', 'updated_by'
    ]
    
    # Inlines
    inlines = [
        PostCategoryInline,
        PostSubCategoryInline,
        PostHashTagInline,
        PostAttachmentInline,
    ]
    
    # Autocomplete fields
    autocomplete_fields = ['organization', 'subsidiary', 'post_type']
    
    # Actions
    actions = ['make_published', 'make_draft', 'feature_posts', 'unfeature_posts']
    
    # Prepopulated fields
    prepopulated_fields = {'slug': ('title',)}
    
    # Date hierarchy
    date_hierarchy = 'published_at'
    
    # Ordering
    ordering = ['-created_at']
    
    # Display methods
    @display(description=_('Title'), ordering='title')
    def title_display(self, obj):
        if obj.title_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.title_ar,
                obj.title or ''
            )
        return obj.title
    
    @display(description=_('Type'), ordering='post_type')
    def post_type_display(self, obj):
        if obj.post_type:
            color = obj.post_type.color or '#666'
            return format_html(
                '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                color,
                obj.post_type.name_ar or obj.post_type.name
            )
        return '-'
    
    @display(description=_('Organization'), ordering='organization')
    def organization_display(self, obj):
        if obj.organization:
            return obj.organization.name_ar or obj.organization.name
        return '-'
    
    @display(description=_('Status'), ordering='status')
    def status_display(self, obj):
        colors = {
            'draft': '#gray',
            'published': '#22c55e',
            'archived': '#f59e0b',
        }
        labels = {
            'draft': _('Draft'),
            'published': _('Published'),
            'archived': _('Archived'),
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#666'),
            labels.get(obj.status, obj.status)
        )
    
    @display(description=_('Featured'), boolean=True)
    def is_featured_display(self, obj):
        return obj.is_featured
    
    # Actions
    @action(description=_('Publish selected posts'))
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, _(f'{updated} posts were published.'))
    
    @action(description=_('Make selected posts draft'))
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, _(f'{updated} posts were made draft.'))
    
    @action(description=_('Feature selected posts'))
    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, _(f'{updated} posts were featured.'))
    
    @action(description=_('Unfeature selected posts'))
    def unfeature_posts(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, _(f'{updated} posts were unfeatured.'))
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'post_type', 'organization', 'subsidiary', 'created_by', 'updated_by'
        ).prefetch_related('categories', 'sub_categories', 'hashtags')


@admin.register(PostType)
class PostTypeAdmin(ModelAdmin):
    """Admin configuration for PostType model"""
    
    list_display = ['name_display', 'color_display', 'icon', 'post_count', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'name_ar', 'description', 'description_ar']
    ordering = ['order', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'name_ar'),
                'slug',
                ('description', 'description_ar'),
            )
        }),
        (_('Appearance'), {
            'fields': (
                ('color', 'icon'),
                'order',
                'is_active',
            )
        }),
        (_('Statistics'), {
            'fields': ('post_count',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['slug', 'post_count']
    prepopulated_fields = {'slug': ('name',)}
    
    @display(description=_('Name'))
    def name_display(self, obj):
        if obj.name_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.name_ar,
                obj.name or ''
            )
        return obj.name
    
    @display(description=_('Color'))
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="background: {}; width: 20px; height: 20px; display: inline-block; border-radius: 3px;"></span> {}',
                obj.color,
                obj.color
            )
        return '-'


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    """Admin configuration for Category model"""
    
    list_display = ['name_display', 'icon', 'post_count', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'name_ar', 'description', 'description_ar']
    ordering = ['order', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'name_ar'),
                'slug',
                ('description', 'description_ar'),
            )
        }),
        (_('Display Settings'), {
            'fields': (
                'icon',
                'order',
                'is_active',
            )
        }),
        (_('Statistics'), {
            'fields': ('post_count',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['slug', 'post_count']
    prepopulated_fields = {'slug': ('name',)}
    
    @display(description=_('Name'))
    def name_display(self, obj):
        if obj.name_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.name_ar,
                obj.name or ''
            )
        return obj.name


@admin.register(SubCategory)
class SubCategoryAdmin(ModelAdmin):
    """Admin configuration for SubCategory model"""
    
    list_display = ['name_display', 'category_display', 'post_count', 'order', 'is_active']
    list_filter = ['is_active', ('category', RelatedDropdownFilter)]
    search_fields = ['name', 'name_ar', 'description', 'description_ar', 'category__name', 'category__name_ar']
    ordering = ['category', 'order', 'name']
    autocomplete_fields = ['category']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'category',
                ('name', 'name_ar'),
                'slug',
                ('description', 'description_ar'),
            )
        }),
        (_('Display Settings'), {
            'fields': (
                'order',
                'is_active',
            )
        }),
        (_('Statistics'), {
            'fields': ('post_count',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['slug', 'post_count']
    prepopulated_fields = {'slug': ('name',)}
    
    @display(description=_('Name'))
    def name_display(self, obj):
        if obj.name_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.name_ar,
                obj.name or ''
            )
        return obj.name
    
    @display(description=_('Category'), ordering='category')
    def category_display(self, obj):
        if obj.category:
            return obj.category.name_ar or obj.category.name
        return '-'


@admin.register(HashTag)
class HashTagAdmin(ModelAdmin):
    """Admin configuration for HashTag model"""
    
    list_display = ['hashtag_display', 'post_count', 'is_trending_display', 'last_used', 'is_active']
    list_filter = ['is_trending', 'is_active', ('last_used', RangeDateFilter)]
    search_fields = ['name']
    ordering = ['-post_count', 'name']
    date_hierarchy = 'last_used'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'slug',
                ('description', 'description_ar'),
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
                'is_trending',
            )
        }),
        (_('Statistics'), {
            'fields': (
                'post_count',
                'last_used',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['slug', 'post_count', 'last_used']
    
    actions = ['mark_trending', 'unmark_trending']
    
    @display(description=_('Hashtag'))
    def hashtag_display(self, obj):
        return format_html('#{} <small style="color: #666;">({})</small>', obj.name, obj.post_count)
    
    @display(description=_('Trending'), boolean=True)
    def is_trending_display(self, obj):
        return obj.is_trending
    
    @action(description=_('Mark as trending'))
    def mark_trending(self, request, queryset):
        updated = queryset.update(is_trending=True)
        self.message_user(request, _(f'{updated} hashtags marked as trending.'))
    
    @action(description=_('Remove from trending'))
    def unmark_trending(self, request, queryset):
        updated = queryset.update(is_trending=False)
        self.message_user(request, _(f'{updated} hashtags removed from trending.'))


@admin.register(PostAttachment)
class PostAttachmentAdmin(ModelAdmin):
    """Admin configuration for PostAttachment model"""
    
    list_display = ['title_display', 'post_display', 'file_type', 'formatted_size', 'is_public', 'download_count', 'created_at']
    list_filter = ['file_type', 'is_public', ('created_at', RangeDateFilter)]
    search_fields = ['title', 'description', 'post__title', 'post__title_ar']
    autocomplete_fields = ['post']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Attachment Information'), {
            'fields': (
                'post',
                'file',
                'title',
                'description',
            )
        }),
        (_('File Details'), {
            'fields': (
                'file_type',
                'size',
                'order',
                'is_public',
            )
        }),
        (_('Statistics'), {
            'fields': (
                'download_count',
                'created_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['file_type', 'size', 'download_count', 'created_at']
    
    @display(description=_('Title'))
    def title_display(self, obj):
        return obj.title or obj.file.name
    
    @display(description=_('Post'))
    def post_display(self, obj):
        if obj.post:
            return obj.post.title_ar or obj.post.title
        return '-'


@admin.register(Bookmark)
class BookmarkAdmin(ModelAdmin):
    """Admin configuration for Bookmark model"""
    
    list_display = ['user', 'post_display', 'created_at']
    list_filter = [('created_at', RangeDateFilter)]
    search_fields = ['user__username', 'user__email', 'post__title', 'post__title_ar', 'notes']
    autocomplete_fields = ['user', 'post']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Bookmark Information'), {
            'fields': (
                'user',
                'post',
                'notes',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @display(description=_('Post'))
    def post_display(self, obj):
        if obj.post:
            return obj.post.title_ar or obj.post.title
        return '-'