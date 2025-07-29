from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models.classification import Category, SubCategory, HashTag
from .models.bookmark import Bookmark
from .models.post import Post, PostType, PostAttachment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_ar', 'description', 'description_ar')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'category', 'slug', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'name_ar', 'description', 'description_ar')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(HashTag)
class HashTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'is_trending', 'last_used')
    list_filter = ('is_trending',)
    search_fields = ('name',)
    readonly_fields = ('post_count', 'is_trending', 'last_used')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title', 'notes')
    raw_id_fields = ('user', 'post')
    date_hierarchy = 'created_at'


class PostAttachmentInline(admin.TabularInline):
    model = PostAttachment
    extra = 1
    fields = ('file', 'title', 'description', 'order')


@admin.register(PostType)
class PostTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_ar', 'description', 'description_ar')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'type', 'organization', 'status', 'created_at', 'published_at')
    list_filter = ('status', 'type', 'organization', 'created_at', 'published_at')
    search_fields = (
        'title', 'title_ar', 'content', 'content_ar',
        'author__username', 'author__email',
        'organization__name', 'subsidiary__name'
    )
    raw_id_fields = ('author', 'organization', 'subsidiary')
    filter_horizontal = ('categories', 'subcategories', 'hashtags')
    readonly_fields = ('slug', 'view_count', 'reading_time', 'created_at', 'updated_at', 'published_at')
    date_hierarchy = 'created_at'
    inlines = [PostAttachmentInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'title', 'title_ar', 'content', 'content_ar',
                'summary', 'summary_ar', 'author'
            )
        }),
        (_('Classification'), {
            'fields': (
                'type', 'organization', 'subsidiary',
                'categories', 'subcategories', 'hashtags'
            )
        }),
        (_('Publication'), {
            'fields': ('status', 'created_at', 'updated_at', 'published_at')
        }),
        (_('SEO'), {
            'fields': ('slug', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        (_('Analytics'), {
            'fields': ('view_count', 'reading_time'),
            'classes': ('collapse',)
        })
    )
