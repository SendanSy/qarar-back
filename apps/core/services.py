"""
Base service classes for the Qarar project.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .exceptions import BusinessLogicError, NotFoundError, PermissionDeniedError
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class BaseService(ABC):
    """
    Base service class that provides common functionality for all services.
    """
    
    def __init__(self, user: Optional[User] = None):
        self.user = user
    
    def _validate_user_permission(self, permission: str) -> None:
        """
        Validate that the current user has the required permission.
        """
        if not self.user:
            raise PermissionDeniedError("Authentication required")
        
        if not self.user.has_perm(permission):
            raise PermissionDeniedError(f"Permission '{permission}' required")
    
    def _validate_business_rules(self, data: Dict[str, Any]) -> None:
        """
        Validate business rules specific to the service.
        Override in subclasses.
        """
        pass
    
    def _log_action(self, action: str, entity_id: Any = None, details: Dict[str, Any] = None) -> None:
        """
        Log service actions for audit purposes.
        """
        logger.info(f"Service Action: {action}", extra={
            'user': self.user.id if self.user else None,
            'entity_id': entity_id,
            'details': details or {},
            'service': self.__class__.__name__,
        })


class CRUDService(BaseService):
    """
    Base CRUD service class for standard database operations.
    """
    model = None
    
    def __init__(self, user: Optional[User] = None):
        super().__init__(user)
        if not self.model:
            raise NotImplementedError("Model must be defined in subclass")
    
    def get_queryset(self):
        """
        Get the base queryset for the model.
        Override in subclasses to add filtering, prefetch, etc.
        """
        return self.model.objects.all()
    
    def get_by_id(self, entity_id: Any) -> Any:
        """
        Get a single entity by ID.
        """
        try:
            return self.get_queryset().get(id=entity_id)
        except self.model.DoesNotExist:
            raise NotFoundError(f"{self.model.__name__} with id {entity_id} not found")
    
    def get_by_slug(self, slug: str) -> Any:
        """
        Get a single entity by slug.
        """
        try:
            return self.get_queryset().get(slug=slug)
        except self.model.DoesNotExist:
            raise NotFoundError(f"{self.model.__name__} with slug {slug} not found")
        except AttributeError:
            raise NotImplementedError("Model does not have slug field")
    
    def list(self, filters: Dict[str, Any] = None, ordering: List[str] = None) -> List[Any]:
        """
        List entities with optional filtering and ordering.
        """
        queryset = self.get_queryset()
        
        if filters:
            queryset = queryset.filter(**filters)
        
        if ordering:
            queryset = queryset.order_by(*ordering)
        
        return list(queryset)
    
    @transaction.atomic
    def create(self, data: Dict[str, Any]) -> Any:
        """
        Create a new entity.
        """
        self._validate_business_rules(data)
        
        # Add audit fields if the model supports them
        if hasattr(self.model, 'created_by') and self.user:
            data['created_by'] = self.user
        
        try:
            instance = self.model(**data)
            instance.full_clean()
            instance.save()
            
            self._log_action('create', instance.id, data)
            return instance
        except ValidationError as e:
            raise BusinessLogicError(f"Validation failed: {e}")
    
    @transaction.atomic
    def update(self, entity_id: Any, data: Dict[str, Any]) -> Any:
        """
        Update an existing entity.
        """
        instance = self.get_by_id(entity_id)
        self._validate_business_rules(data)
        
        # Add audit fields if the model supports them
        if hasattr(self.model, 'updated_by') and self.user:
            data['updated_by'] = self.user
        
        try:
            for field, value in data.items():
                setattr(instance, field, value)
            
            instance.full_clean()
            instance.save()
            
            self._log_action('update', entity_id, data)
            return instance
        except ValidationError as e:
            raise BusinessLogicError(f"Validation failed: {e}")
    
    @transaction.atomic
    def delete(self, entity_id: Any, hard_delete: bool = False) -> None:
        """
        Delete an entity (soft delete by default if supported).
        """
        instance = self.get_by_id(entity_id)
        
        if hard_delete or not hasattr(instance, 'delete'):
            instance.delete()
            action = 'hard_delete'
        else:
            # Use soft delete if available
            if hasattr(instance, 'is_deleted'):
                instance.delete()  # This will be soft delete
                action = 'soft_delete'
            else:
                instance.delete()
                action = 'delete'
        
        self._log_action(action, entity_id)
    
    def exists(self, **kwargs) -> bool:
        """
        Check if an entity exists with the given criteria.
        """
        return self.get_queryset().filter(**kwargs).exists()
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count entities with optional filtering.
        """
        queryset = self.get_queryset()
        
        if filters:
            queryset = queryset.filter(**filters)
        
        return queryset.count()


class PublishableService(CRUDService):
    """
    Service for models that have publishing functionality.
    """
    
    def _validate_publish_permission(self) -> None:
        """
        Validate that the user can publish content.
        """
        self._validate_user_permission('content.publish_content')
    
    @transaction.atomic
    def publish(self, entity_id: Any) -> Any:
        """
        Publish an entity.
        """
        self._validate_publish_permission()
        
        instance = self.get_by_id(entity_id)
        
        if not hasattr(instance, 'publish'):
            raise NotImplementedError("Model does not support publishing")
        
        if instance.is_published:
            raise BusinessLogicError("Content is already published")
        
        instance.publish(user=self.user)
        
        self._log_action('publish', entity_id)
        return instance
    
    @transaction.atomic
    def unpublish(self, entity_id: Any) -> Any:
        """
        Unpublish an entity.
        """
        self._validate_publish_permission()
        
        instance = self.get_by_id(entity_id)
        
        if not hasattr(instance, 'unpublish'):
            raise NotImplementedError("Model does not support unpublishing")
        
        if not instance.is_published:
            raise BusinessLogicError("Content is not published")
        
        instance.unpublish()
        
        self._log_action('unpublish', entity_id)
        return instance
    
    def get_published(self, filters: Dict[str, Any] = None) -> List[Any]:
        """
        Get only published entities.
        """
        published_filters = {'status': 'published'}
        if filters:
            published_filters.update(filters)
        
        return self.list(published_filters)
    
    def get_drafts(self, filters: Dict[str, Any] = None) -> List[Any]:
        """
        Get only draft entities.
        """
        draft_filters = {'status': 'draft'}
        if filters:
            draft_filters.update(filters)
        
        return self.list(draft_filters)


class ViewTrackingService(BaseService):
    """
    Service for tracking views on content.
    """
    
    def __init__(self, model_class, user: Optional[User] = None):
        super().__init__(user)
        self.model_class = model_class
    
    def track_view(self, entity_id: Any, user_id: Optional[Any] = None) -> None:
        """
        Track a view for an entity.
        """
        try:
            instance = self.model_class.objects.get(id=entity_id)
            
            if not hasattr(instance, 'increment_view_count'):
                raise NotImplementedError("Model does not support view tracking")
            
            instance.increment_view_count()
            
            self._log_action('view', entity_id, {'user_id': user_id})
            
        except self.model_class.DoesNotExist:
            raise NotFoundError(f"Entity with id {entity_id} not found")
    
    def get_view_stats(self, entity_id: Any) -> Dict[str, Any]:
        """
        Get view statistics for an entity.
        """
        try:
            instance = self.model_class.objects.get(id=entity_id)
            
            return {
                'view_count': getattr(instance, 'view_count', 0),
                'last_viewed_at': getattr(instance, 'last_viewed_at', None),
            }
        except self.model_class.DoesNotExist:
            raise NotFoundError(f"Entity with id {entity_id} not found")


class SearchService(BaseService):
    """
    Base service for search functionality.
    """
    
    def __init__(self, model_class, user: Optional[User] = None):
        super().__init__(user)
        self.model_class = model_class
    
    def search(self, query: str, filters: Dict[str, Any] = None, limit: int = 20) -> List[Any]:
        """
        Search for entities using the given query.
        Override in subclasses to implement specific search logic.
        """
        queryset = self.model_class.objects.all()
        
        if filters:
            queryset = queryset.filter(**filters)
        
        # Basic search implementation - override in subclasses
        search_fields = getattr(self.model_class, 'search_fields', [])
        if search_fields and query:
            from django.db.models import Q
            search_query = Q()
            for field in search_fields:
                search_query |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(search_query)
        
        return list(queryset[:limit])
    
    def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on the query.
        Override in subclasses to implement specific suggestion logic.
        """
        # Basic implementation - can be enhanced with search analytics
        return []