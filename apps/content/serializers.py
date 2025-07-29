from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from apps.users.serializers import UserMinimalSerializer
from apps.producers.models import Organization, Subsidiary, Department
from .models.classification import Category, SubCategory, HashTag
from .models.bookmark import Bookmark
from .models.post import Post, PostType, PostAttachment

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for content categories
    """
    post_count = serializers.SerializerMethodField()
    subcategory_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'name_ar', 'slug', 'description', 'description_ar',
                 'icon', 'is_active', 'post_count', 'subcategory_count')
        read_only_fields = ('slug', 'post_count', 'subcategory_count')
    
    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()
    
    def get_subcategory_count(self, obj):
        return obj.subcategories.count()


class SubCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for content sub-categories
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_name_ar = serializers.CharField(source='category.name_ar', read_only=True)
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SubCategory
        fields = ('id', 'category', 'category_name', 'category_name_ar',
                 'name', 'name_ar', 'slug', 'description', 'description_ar',
                 'is_active', 'post_count')
        read_only_fields = ('slug', 'post_count')
    
    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()


class HashTagSerializer(serializers.ModelSerializer):
    """
    Serializer for hashtags
    """
    class Meta:
        model = HashTag
        fields = ('id', 'name', 'slug', 'post_count', 'is_trending', 'last_used')
        read_only_fields = ('slug', 'post_count', 'is_trending', 'last_used')


class PostTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for post types
    """
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PostType
        fields = ('id', 'name', 'name_ar', 'description', 'description_ar',
                 'is_active', 'post_count')
        read_only_fields = ('post_count',)
    
    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()


class PostAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for post attachments
    """
    file_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    
    class Meta:
        model = PostAttachment
        fields = ('id', 'file', 'file_url', 'title', 'description', 'file_type',
                 'size', 'file_size_display', 'file_extension', 'order', 'created_at')
        read_only_fields = ('file_type', 'size', 'created_at', 'file_extension')
    
    def get_file_url(self, obj):
        if not obj.file:
            return None
        
        # If using S3, the file.url already contains the full URL
        if hasattr(obj.file, 'url'):
            file_url = obj.file.url
            # Check if it's already a full URL (S3 or CloudFront)
            if file_url.startswith('http'):
                return file_url
        
        # For local storage, build absolute URI
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
    
    def get_file_size_display(self, obj):
        """Convert file size to human readable format"""
        if not obj.size:
            return '0 B'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.size < 1024:
                return f"{obj.size:.1f} {unit}"
            obj.size /= 1024
        return f"{obj.size:.1f} TB"
    
    def get_file_extension(self, obj):
        """Get file extension"""
        if obj.file:
            return obj.file.name.split('.')[-1].lower()
        return None


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for posts
    """
    author = UserMinimalSerializer(read_only=True)
    type = PostTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        source='type',
        queryset=PostType.objects.filter(is_active=True),
        write_only=True
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.filter(is_active=True)
    )
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_name_ar = serializers.CharField(source='organization.name_ar', read_only=True)
    subsidiary = serializers.PrimaryKeyRelatedField(
        queryset=Subsidiary.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    subsidiary_name = serializers.CharField(source='subsidiary.name', read_only=True)
    subsidiary_name_ar = serializers.CharField(source='subsidiary.name_ar', read_only=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_name_ar = serializers.CharField(source='department.name_ar', read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories',
        queryset=Category.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False
    )
    subcategories = SubCategorySerializer(many=True, read_only=True)
    subcategory_ids = serializers.PrimaryKeyRelatedField(
        source='subcategories',
        queryset=SubCategory.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False
    )
    hashtags = HashTagSerializer(many=True, read_only=True)
    hashtag_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    attachments = PostAttachmentSerializer(many=True, read_only=True)
    reading_time = serializers.IntegerField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = (
            'id', 'title', 'title_ar', 'content', 'content_ar', 'summary', 'summary_ar',
            'author', 'type', 'type_id', 'organization', 'organization_name',
            'organization_name_ar', 'subsidiary', 'subsidiary_name', 'subsidiary_name_ar',
            'department', 'department_name', 'department_name_ar',
            'categories', 'category_ids', 'subcategories', 'subcategory_ids',
            'hashtags', 'hashtag_names', 'attachments', 'attachment_count',
            'status', 'created_at', 'updated_at', 'published_at', 'view_count',
            'slug', 'meta_description', 'meta_keywords', 'reading_time', 'is_bookmarked'
        )
        read_only_fields = (
            'author', 'created_at', 'updated_at', 'published_at',
            'view_count', 'slug', 'reading_time', 'is_bookmarked',
            'attachment_count'
        )
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Explicitly check for non-deleted bookmarks
            return Bookmark.objects.filter(
                user=request.user, 
                post=obj,
                is_deleted=False
            ).exists()
        return False
    
    def get_attachment_count(self, obj):
        return obj.attachments.count()
    
    def create(self, validated_data):
        hashtag_names = validated_data.pop('hashtag_names', [])
        instance = super().create(validated_data)
        
        # Handle hashtags
        if hashtag_names:
            for name in hashtag_names:
                hashtag, _ = HashTag.objects.get_or_create(name=name)
                instance.hashtags.add(hashtag)
        
        return instance
    
    def update(self, instance, validated_data):
        hashtag_names = validated_data.pop('hashtag_names', None)
        instance = super().update(instance, validated_data)
        
        # Handle hashtags
        if hashtag_names is not None:
            instance.hashtags.clear()
            for name in hashtag_names:
                hashtag, _ = HashTag.objects.get_or_create(name=name)
                instance.hashtags.add(hashtag)
        
        return instance


class BookmarkSerializer(serializers.ModelSerializer):
    """
    Serializer for bookmarked content
    """
    post = PostSerializer(read_only=True)
    post_id = serializers.PrimaryKeyRelatedField(
        source='post',
        queryset=Post.objects.all(),
        write_only=True
    )
    
    class Meta:
        model = Bookmark
        fields = ('id', 'post', 'post_id', 'created_at', 'notes')
        read_only_fields = ('created_at',) 