"""
Bulk operations for efficient API operations.
"""
from typing import List, Dict, Any, Union
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.services import BaseService
from apps.core.exceptions import BusinessLogicError, ValidationError as CustomValidationError
from .models.post import Post, PostAttachment
from .models.classification import Category, SubCategory, HashTag
from .models.bookmark import Bookmark
from .services import PostService

User = get_user_model()


class BulkOperationService(BaseService):
    """
    Service for handling bulk operations efficiently.
    """
    
    def __init__(self, user: User = None):
        super().__init__(user)
        self.post_service = PostService(user)
    
    @transaction.atomic
    def bulk_create_posts(self, posts_data: List[Dict[str, Any]]) -> List[Post]:
        """
        Create multiple posts efficiently.
        
        Args:
            posts_data: List of post data dictionaries
            
        Returns:
            List of created Post instances
        """
        if not posts_data:
            return []
        
        if len(posts_data) > 100:  # Limit bulk operations
            raise BusinessLogicError("Cannot create more than 100 posts at once")
        
        created_posts = []
        errors = []
        
        for i, post_data in enumerate(posts_data):
            try:
                # Validate required fields
                self._validate_post_data(post_data)
                
                # Create post using service
                post = self.post_service.create_post(post_data)
                created_posts.append(post)
                
            except Exception as e:
                errors.append(f"Post {i}: {str(e)}")
        
        if errors:
            raise CustomValidationError(
                f"Bulk creation failed with {len(errors)} errors",
                details={'errors': errors}
            )
        
        self._log_action('bulk_create_posts', details={
            'count': len(created_posts),
            'post_ids': [str(p.id) for p in created_posts]
        })
        
        return created_posts
    
    @transaction.atomic
    def bulk_update_posts(self, updates: List[Dict[str, Any]]) -> List[Post]:
        """
        Update multiple posts efficiently.
        
        Args:
            updates: List of dictionaries with 'id' and update data
            
        Returns:
            List of updated Post instances
        """
        if not updates:
            return []
        
        if len(updates) > 100:
            raise BusinessLogicError("Cannot update more than 100 posts at once")
        
        updated_posts = []
        errors = []
        
        for i, update_data in enumerate(updates):
            try:
                post_id = update_data.pop('id')
                post = self.post_service.update_post(post_id, update_data)
                updated_posts.append(post)
                
            except Exception as e:
                errors.append(f"Update {i}: {str(e)}")
        
        if errors:
            raise CustomValidationError(
                f"Bulk update failed with {len(errors)} errors",
                details={'errors': errors}
            )
        
        self._log_action('bulk_update_posts', details={
            'count': len(updated_posts),
            'post_ids': [str(p.id) for p in updated_posts]
        })
        
        return updated_posts
    
    @transaction.atomic
    def bulk_publish_posts(self, post_ids: List[str]) -> List[Post]:
        """
        Publish multiple posts efficiently.
        
        Args:
            post_ids: List of post IDs to publish
            
        Returns:
            List of published Post instances
        """
        if not post_ids:
            return []
        
        if len(post_ids) > 50:  # Smaller limit for publishing
            raise BusinessLogicError("Cannot publish more than 50 posts at once")
        
        # Check permissions
        self._validate_user_permission('content.publish_content')
        
        # Get posts and validate
        posts = Post.objects.filter(
            id__in=post_ids,
            is_deleted=False
        ).select_related('author', 'organization')
        
        if len(posts) != len(post_ids):
            raise BusinessLogicError("Some posts not found or already deleted")
        
        # Check individual permissions
        for post in posts:
            if not self._can_publish_post(post):
                raise BusinessLogicError(f"No permission to publish post {post.id}")
        
        # Bulk update status and published_at
        now = timezone.now()
        updated_count = posts.filter(status__in=['draft', 'pending']).update(
            status='published',
            published_at=now,
            updated_at=now
        )
        
        # Refresh instances
        published_posts = list(posts.filter(status='published'))
        
        self._log_action('bulk_publish_posts', details={
            'count': updated_count,
            'post_ids': post_ids
        })
        
        return published_posts
    
    @transaction.atomic
    def bulk_delete_posts(self, post_ids: List[str], hard_delete: bool = False) -> int:
        """
        Delete multiple posts efficiently.
        
        Args:
            post_ids: List of post IDs to delete
            hard_delete: Whether to permanently delete or soft delete
            
        Returns:
            Number of deleted posts
        """
        if not post_ids:
            return 0
        
        if len(post_ids) > 100:
            raise BusinessLogicError("Cannot delete more than 100 posts at once")
        
        # Get posts and validate permissions
        posts = Post.objects.filter(id__in=post_ids, is_deleted=False)
        
        for post in posts:
            if not self._can_delete_post(post):
                raise BusinessLogicError(f"No permission to delete post {post.id}")
        
        if hard_delete:
            deleted_count = posts.count()
            posts.delete()
        else:
            # Soft delete
            now = timezone.now()
            deleted_count = posts.update(
                is_deleted=True,
                deleted_at=now,
                updated_at=now
            )
        
        self._log_action('bulk_delete_posts', details={
            'count': deleted_count,
            'post_ids': post_ids,
            'hard_delete': hard_delete
        })
        
        return deleted_count
    
    @transaction.atomic
    def bulk_categorize_posts(self, post_ids: List[str], 
                            category_ids: List[str],
                            action: str = 'add') -> int:
        """
        Add or remove categories from multiple posts.
        
        Args:
            post_ids: List of post IDs
            category_ids: List of category IDs
            action: 'add' or 'remove'
            
        Returns:
            Number of posts affected
        """
        if not post_ids or not category_ids:
            return 0
        
        if action not in ['add', 'remove']:
            raise BusinessLogicError("Action must be 'add' or 'remove'")
        
        # Get posts and categories
        posts = Post.objects.filter(id__in=post_ids, is_deleted=False)
        categories = Category.objects.filter(id__in=category_ids, is_deleted=False, is_active=True)
        
        if not posts.exists():
            raise BusinessLogicError("No valid posts found")
        
        if not categories.exists():
            raise BusinessLogicError("No valid categories found")
        
        affected_count = 0
        
        for post in posts:
            if not self._can_edit_post(post):
                continue
            
            if action == 'add':
                post.categories.add(*categories)
            else:  # remove
                post.categories.remove(*categories)
            
            affected_count += 1
        
        # Update category post counts
        for category in categories:
            category.update_post_count()
        
        self._log_action(f'bulk_{action}_categories', details={
            'post_count': affected_count,
            'category_count': len(categories)
        })
        
        return affected_count
    
    @transaction.atomic
    def bulk_create_bookmarks(self, bookmark_data: List[Dict[str, Any]]) -> List[Bookmark]:
        """
        Create multiple bookmarks efficiently.
        
        Args:
            bookmark_data: List of bookmark data dictionaries
            
        Returns:
            List of created Bookmark instances
        """
        if not bookmark_data:
            return []
        
        if len(bookmark_data) > 100:
            raise BusinessLogicError("Cannot create more than 100 bookmarks at once")
        
        # Validate data and prepare for bulk creation
        bookmarks_to_create = []
        post_ids = []
        
        for data in bookmark_data:
            if 'post_id' not in data:
                raise ValidationError("post_id is required for each bookmark")
            
            post_ids.append(data['post_id'])
            
            bookmark = Bookmark(
                user=self.user,
                post_id=data['post_id'],
                notes=data.get('notes', ''),
                tags=data.get('tags', ''),
                is_private=data.get('is_private', True)
            )
            bookmarks_to_create.append(bookmark)
        
        # Validate that all posts exist and are published
        existing_posts = Post.objects.filter(
            id__in=post_ids,
            status='published',
            is_deleted=False
        ).values_list('id', flat=True)
        
        if len(existing_posts) != len(post_ids):
            missing_posts = set(post_ids) - set(existing_posts)
            raise BusinessLogicError(f"Posts not found or not published: {missing_posts}")
        
        # Bulk create bookmarks
        try:
            created_bookmarks = Bookmark.objects.bulk_create(
                bookmarks_to_create,
                ignore_conflicts=True  # Ignore duplicates
            )
            
            self._log_action('bulk_create_bookmarks', details={
                'count': len(created_bookmarks)
            })
            
            return created_bookmarks
            
        except Exception as e:
            raise BusinessLogicError(f"Failed to create bookmarks: {str(e)}")
    
    def bulk_export_posts(self, post_ids: List[str], format: str = 'json') -> Dict[str, Any]:
        """
        Export multiple posts in specified format.
        
        Args:
            post_ids: List of post IDs to export
            format: Export format ('json', 'csv', 'xml')
            
        Returns:
            Dictionary with export data
        """
        if not post_ids:
            return {'data': [], 'count': 0}
        
        if len(post_ids) > 500:
            raise BusinessLogicError("Cannot export more than 500 posts at once")
        
        # Get posts with related data
        posts = Post.objects.filter(
            id__in=post_ids,
            is_deleted=False
        ).select_related(
            'author', 'type', 'organization', 'subsidiary'
        ).prefetch_related(
            'categories', 'subcategories', 'hashtags', 'attachments'
        )
        
        # Check permissions
        accessible_posts = []
        for post in posts:
            if self._can_view_post(post):
                accessible_posts.append(post)
        
        if format == 'json':
            return self._export_posts_json(accessible_posts)
        elif format == 'csv':
            return self._export_posts_csv(accessible_posts)
        elif format == 'xml':
            return self._export_posts_xml(accessible_posts)
        else:
            raise BusinessLogicError(f"Unsupported export format: {format}")
    
    def _validate_post_data(self, post_data: Dict[str, Any]) -> None:
        """Validate post data for bulk operations."""
        required_fields = ['title', 'content', 'organization', 'type']
        
        for field in required_fields:
            if field not in post_data or not post_data[field]:
                raise ValidationError(f"Required field missing: {field}")
    
    def _can_publish_post(self, post: Post) -> bool:
        """Check if user can publish the post."""
        if not self.user:
            return False
        
        if self.user.is_superuser:
            return True
        
        # Author can publish their own posts
        if post.author == self.user:
            return True
        
        # Check organization permissions
        return self._has_organization_permission(post.organization, ['admin', 'editor'])
    
    def _can_delete_post(self, post: Post) -> bool:
        """Check if user can delete the post."""
        if not self.user:
            return False
        
        if self.user.is_superuser:
            return True
        
        # Author can delete their own posts
        if post.author == self.user:
            return True
        
        # Organization admin can delete posts
        return self._has_organization_permission(post.organization, ['admin'])
    
    def _can_edit_post(self, post: Post) -> bool:
        """Check if user can edit the post."""
        if not self.user:
            return False
        
        if self.user.is_superuser:
            return True
        
        # Author can edit their own posts
        if post.author == self.user:
            return True
        
        # Organization editors can edit posts
        return self._has_organization_permission(post.organization, ['admin', 'editor'])
    
    def _can_view_post(self, post: Post) -> bool:
        """Check if user can view the post."""
        # Published posts are generally viewable
        if post.status == 'published':
            return True
        
        if not self.user:
            return False
        
        # Author can view their own posts
        if post.author == self.user:
            return True
        
        # Organization members can view drafts
        return self._has_organization_permission(post.organization, ['admin', 'editor', 'viewer'])
    
    def _has_organization_permission(self, organization, roles: List[str]) -> bool:
        """Check if user has organization permission."""
        if not self.user:
            return False
        
        # This would need to be implemented based on your organization membership model
        # For now, return True for superusers
        return self.user.is_superuser
    
    def _export_posts_json(self, posts: List[Post]) -> Dict[str, Any]:
        """Export posts as JSON."""
        # Simple dictionary export instead of using complex serializer
        data = []
        for post in posts:
            data.append({
                'id': str(post.id),
                'title': post.title,
                'title_ar': post.title_ar,
                'content': post.content,
                'status': post.status,
                'author': post.author.username if post.author else None,
                'organization': post.organization.name if post.organization else None,
                'type': post.type.name if post.type else None,
                'created_at': post.created_at.isoformat(),
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'view_count': post.view_count
            })
        
        return {
            'format': 'json',
            'count': len(posts),
            'data': data,
            'exported_at': timezone.now().isoformat()
        }
    
    def _export_posts_csv(self, posts: List[Post]) -> Dict[str, Any]:
        """Export posts as CSV data."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Title', 'Title (Arabic)', 'Status', 'Author',
            'Organization', 'Type', 'Created At', 'Published At', 'View Count'
        ])
        
        # Write data
        for post in posts:
            writer.writerow([
                str(post.id),
                post.title,
                post.title_ar or '',
                post.status,
                post.author.username,
                post.organization.name,
                post.type.name,
                post.created_at.isoformat(),
                post.published_at.isoformat() if post.published_at else '',
                post.view_count
            ])
        
        return {
            'format': 'csv',
            'count': len(posts),
            'data': output.getvalue(),
            'exported_at': timezone.now().isoformat()
        }
    
    def _export_posts_xml(self, posts: List[Post]) -> Dict[str, Any]:
        """Export posts as XML data."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('posts')
        root.set('count', str(len(posts)))
        root.set('exported_at', timezone.now().isoformat())
        
        for post in posts:
            post_elem = ET.SubElement(root, 'post')
            post_elem.set('id', str(post.id))
            
            ET.SubElement(post_elem, 'title').text = post.title
            ET.SubElement(post_elem, 'title_ar').text = post.title_ar or ''
            ET.SubElement(post_elem, 'status').text = post.status
            ET.SubElement(post_elem, 'author').text = post.author.username
            ET.SubElement(post_elem, 'organization').text = post.organization.name
            ET.SubElement(post_elem, 'type').text = post.type.name
            ET.SubElement(post_elem, 'created_at').text = post.created_at.isoformat()
            ET.SubElement(post_elem, 'view_count').text = str(post.view_count)
        
        return {
            'format': 'xml',
            'count': len(posts),
            'data': ET.tostring(root, encoding='unicode'),
            'exported_at': timezone.now().isoformat()
        }


class BulkImportService(BaseService):
    """
    Service for handling bulk imports.
    """
    
    def __init__(self, user: User = None):
        super().__init__(user)
        self.bulk_service = BulkOperationService(user)
    
    def import_posts_from_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import posts from JSON data.
        
        Args:
            json_data: JSON data containing posts
            
        Returns:
            Import results dictionary
        """
        if 'data' not in json_data:
            raise ValidationError("JSON data must contain 'data' field")
        
        posts_data = json_data['data']
        
        if not isinstance(posts_data, list):
            raise ValidationError("Posts data must be a list")
        
        # Clean and validate data
        cleaned_posts = []
        for post_data in posts_data:
            cleaned_post = self._clean_import_data(post_data)
            cleaned_posts.append(cleaned_post)
        
        # Import posts
        try:
            created_posts = self.bulk_service.bulk_create_posts(cleaned_posts)
            
            return {
                'success': True,
                'imported_count': len(created_posts),
                'post_ids': [str(p.id) for p in created_posts],
                'errors': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'imported_count': 0,
                'post_ids': [],
                'errors': [str(e)]
            }
    
    def import_posts_from_csv(self, csv_data: str) -> Dict[str, Any]:
        """
        Import posts from CSV data.
        
        Args:
            csv_data: CSV string data
            
        Returns:
            Import results dictionary
        """
        import csv
        import io
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_data))
        posts_data = []
        
        for row in reader:
            post_data = self._csv_row_to_post_data(row)
            posts_data.append(post_data)
        
        # Import posts
        try:
            created_posts = self.bulk_service.bulk_create_posts(posts_data)
            
            return {
                'success': True,
                'imported_count': len(created_posts),
                'post_ids': [str(p.id) for p in created_posts],
                'errors': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'imported_count': 0,
                'post_ids': [],
                'errors': [str(e)]
            }
    
    def _clean_import_data(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate import data."""
        from apps.producers.models import Organization
        from .models.post import PostType
        
        # Remove read-only fields
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'published_at',
            'view_count', 'slug', 'author'
        ]
        
        cleaned_data = {}
        for key, value in post_data.items():
            if key not in read_only_fields and value is not None:
                # Convert string IDs to objects if needed
                if key == 'organization' and isinstance(value, str):
                    try:
                        cleaned_data[key] = Organization.objects.get(id=value)
                    except Organization.DoesNotExist:
                        raise ValidationError(f"Organization with ID {value} not found")
                elif key == 'type' and isinstance(value, str):
                    try:
                        cleaned_data[key] = PostType.objects.get(id=value)
                    except PostType.DoesNotExist:
                        raise ValidationError(f"PostType with ID {value} not found")
                else:
                    cleaned_data[key] = value
        
        # Set default values
        cleaned_data.setdefault('status', 'draft')
        
        return cleaned_data
    
    def _csv_row_to_post_data(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Convert CSV row to post data."""
        from apps.producers.models import Organization
        from .models.post import PostType
        
        # Map CSV columns to model fields
        field_mapping = {
            'Title': 'title',
            'Title (Arabic)': 'title_ar',
            'Content': 'content',
            'Content (Arabic)': 'content_ar',
            'Summary': 'summary',
            'Summary (Arabic)': 'summary_ar',
            'Status': 'status',
        }
        
        post_data = {}
        for csv_field, model_field in field_mapping.items():
            if csv_field in row and row[csv_field]:
                post_data[model_field] = row[csv_field]
        
        # Convert IDs to objects
        if 'Organization ID' in row and row['Organization ID']:
            try:
                post_data['organization'] = Organization.objects.get(id=row['Organization ID'])
            except Organization.DoesNotExist:
                raise ValidationError(f"Organization with ID {row['Organization ID']} not found")
                
        if 'Type ID' in row and row['Type ID']:
            try:
                post_data['type'] = PostType.objects.get(id=row['Type ID'])
            except PostType.DoesNotExist:
                raise ValidationError(f"PostType with ID {row['Type ID']} not found")
        
        return post_data