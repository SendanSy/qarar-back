"""
Testing utilities and base test classes.
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
import json
from typing import Dict, Any, Optional, List

from .factories import (
    UserFactory, AdminUserFactory, OrganizationFactory,
    CategoryFactory, PostFactory, PublishedPostFactory,
    create_minimal_test_data, create_test_dataset
)

User = get_user_model()


class BaseTestCase(TestCase):
    """
    Base test case with common utilities.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Clear cache before each test
        cache.clear()
        
        # Create basic test data
        self.user = UserFactory()
        self.admin_user = AdminUserFactory()
        self.organization = OrganizationFactory()
        self.category = CategoryFactory()
    
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        cache.clear()
    
    def assertFieldError(self, form, field, error_code):
        """Assert that a specific field has a specific error."""
        self.assertIn(field, form.errors)
        field_errors = form.errors[field]
        error_codes = [error.code for error in field_errors]
        self.assertIn(error_code, error_codes)
    
    def assertValidationError(self, obj, field=None, code=None):
        """Assert that validation raises an error."""
        from django.core.exceptions import ValidationError
        
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        
        if field:
            self.assertIn(field, cm.exception.message_dict)
        
        if code:
            if field:
                field_errors = cm.exception.message_dict[field]
                error_codes = [error.code for error in field_errors]
                self.assertIn(code, error_codes)
    
    def create_test_post(self, **kwargs):
        """Create a test post with defaults."""
        defaults = {
            'author': self.user,
            'organization': self.organization,
            'categories': [self.category]
        }
        defaults.update(kwargs)
        return PublishedPostFactory(**defaults)


class BaseAPITestCase(APITestCase):
    """
    Base API test case with authentication utilities.
    """
    
    def setUp(self):
        """Set up API test data."""
        super().setUp()
        # Clear cache before each test
        cache.clear()
        
        # Create test users
        self.user = UserFactory()
        self.admin_user = AdminUserFactory()
        self.staff_user = UserFactory(is_staff=True)
        
        # Create basic test data
        self.test_data = create_minimal_test_data()
        
        # Set up API client
        self.client = APIClient()
    
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        cache.clear()
    
    def authenticate(self, user=None):
        """Authenticate a user with JWT."""
        user = user or self.user
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return refresh.access_token
    
    def authenticate_admin(self):
        """Authenticate as admin user."""
        return self.authenticate(self.admin_user)
    
    def authenticate_staff(self):
        """Authenticate as staff user."""
        return self.authenticate(self.staff_user)
    
    def logout(self):
        """Clear authentication credentials."""
        self.client.credentials()
    
    def get_json_response(self, response):
        """Get JSON data from response."""
        return json.loads(response.content.decode('utf-8'))
    
    def assertResponseSuccess(self, response, status_code=status.HTTP_200_OK):
        """Assert response is successful."""
        self.assertEqual(response.status_code, status_code)
        data = self.get_json_response(response)
        self.assertTrue(data.get('success', True))
        return data
    
    def assertResponseError(self, response, status_code=status.HTTP_400_BAD_REQUEST,
                           error_code=None):
        """Assert response is an error."""
        self.assertEqual(response.status_code, status_code)
        data = self.get_json_response(response)
        self.assertFalse(data.get('success', True))
        
        if error_code:
            self.assertEqual(data.get('error', {}).get('code'), error_code)
        
        return data
    
    def assertPaginatedResponse(self, response, expected_count=None):
        """Assert response is paginated."""
        data = self.assertResponseSuccess(response)
        self.assertIn('results', data['data'])
        self.assertIn('count', data['data'])
        self.assertIn('next', data['data'])
        self.assertIn('previous', data['data'])
        
        if expected_count is not None:
            self.assertEqual(len(data['data']['results']), expected_count)
        
        return data
    
    def assertRequiresAuthentication(self, method, url, data=None):
        """Assert endpoint requires authentication."""
        self.logout()
        
        if method.upper() == 'GET':
            response = self.client.get(url)
        elif method.upper() == 'POST':
            response = self.client.post(url, data=data or {})
        elif method.upper() == 'PUT':
            response = self.client.put(url, data=data or {})
        elif method.upper() == 'PATCH':
            response = self.client.patch(url, data=data or {})
        elif method.upper() == 'DELETE':
            response = self.client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def assertRequiresPermission(self, method, url, data=None, user=None):
        """Assert endpoint requires specific permission."""
        test_user = user or self.user
        self.authenticate(test_user)
        
        if method.upper() == 'GET':
            response = self.client.get(url)
        elif method.upper() == 'POST':
            response = self.client.post(url, data=data or {})
        elif method.upper() == 'PUT':
            response = self.client.put(url, data=data or {})
        elif method.upper() == 'PATCH':
            response = self.client.patch(url, data=data or {})
        elif method.upper() == 'DELETE':
            response = self.client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND  # Sometimes used instead of 403
        ])


class ServiceTestCase(BaseTestCase):
    """
    Base test case for testing service classes.
    """
    
    def setUp(self):
        """Set up service test data."""
        super().setUp()
        self.service_user = self.user
    
    def create_service(self, service_class, user=None):
        """Create a service instance."""
        return service_class(user or self.service_user)
    
    def assert_service_error(self, service_method, exception_class, *args, **kwargs):
        """Assert that a service method raises a specific exception."""
        with self.assertRaises(exception_class):
            service_method(*args, **kwargs)


class CacheTestMixin:
    """
    Mixin for testing cache functionality.
    """
    
    def setUp(self):
        super().setUp()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
        super().tearDown()
    
    def assertCached(self, cache_key, expected_value=None):
        """Assert that a value is cached."""
        cached_value = cache.get(cache_key)
        self.assertIsNotNone(cached_value, f"Value not found in cache for key: {cache_key}")
        
        if expected_value is not None:
            self.assertEqual(cached_value, expected_value)
        
        return cached_value
    
    def assertNotCached(self, cache_key):
        """Assert that a value is not cached."""
        cached_value = cache.get(cache_key)
        self.assertIsNone(cached_value, f"Unexpected value found in cache for key: {cache_key}")
    
    def mock_cache_get(self, return_value=None):
        """Mock cache.get method."""
        return patch('django.core.cache.cache.get', return_value=return_value)
    
    def mock_cache_set(self):
        """Mock cache.set method."""
        return patch('django.core.cache.cache.set', return_value=True)


class DatabaseTestMixin:
    """
    Mixin for testing database operations.
    """
    
    def assertQueryCount(self, num, func, *args, **kwargs):
        """Assert the number of database queries."""
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            initial_queries = len(connection.queries)
            func(*args, **kwargs)
            final_queries = len(connection.queries)
            
            query_count = final_queries - initial_queries
            self.assertEqual(
                query_count, num,
                f"Expected {num} queries, but {query_count} were executed.\n"
                f"Queries: {connection.queries[initial_queries:]}"
            )
    
    def assertMaxQueryCount(self, max_num, func, *args, **kwargs):
        """Assert maximum number of database queries."""
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            initial_queries = len(connection.queries)
            func(*args, **kwargs)
            final_queries = len(connection.queries)
            
            query_count = final_queries - initial_queries
            self.assertLessEqual(
                query_count, max_num,
                f"Expected at most {max_num} queries, but {query_count} were executed.\n"
                f"Queries: {connection.queries[initial_queries:]}"
            )
    
    def print_queries(self, func, *args, **kwargs):
        """Print all queries executed by a function (for debugging)."""
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            initial_queries = len(connection.queries)
            result = func(*args, **kwargs)
            final_queries = len(connection.queries)
            
            queries = connection.queries[initial_queries:]
            print(f"\n--- Executed {len(queries)} queries ---")
            for i, query in enumerate(queries, 1):
                print(f"{i}. {query['sql'][:100]}...")
            print("--- End queries ---\n")
            
            return result


class SearchTestMixin:
    """
    Mixin for testing search functionality.
    """
    
    def create_search_test_data(self):
        """Create test data for search tests."""
        # Create posts with specific titles for search testing
        self.search_posts = [
            PostFactory(
                title="Django REST Framework Tutorial",
                content="Learn how to build APIs with Django REST Framework",
                status='published'
            ),
            PostFactory(
                title="Python Web Development",
                content="Complete guide to web development with Python",
                status='published'
            ),
            PostFactory(
                title="API Design Best Practices",
                content="How to design RESTful APIs that scale",
                status='published'
            ),
        ]
        
        # Create posts with Arabic content
        self.arabic_posts = [
            PostFactory(
                title_ar="تطوير المواقع باستخدام جانغو",
                content_ar="دليل شامل لتطوير المواقع",
                status='published'
            ),
            PostFactory(
                title_ar="برمجة تطبيقات الويب",
                content_ar="كيفية إنشاء تطبيقات ويب متقدمة",
                status='published'
            ),
        ]
    
    def assertSearchResults(self, query, expected_count, search_service=None):
        """Assert search results count."""
        if search_service is None:
            from apps.core.search import PostSearchService
            search_service = PostSearchService()
        
        results = search_service.search(query)
        self.assertEqual(
            len(results['results']), expected_count,
            f"Expected {expected_count} results for query '{query}', got {len(results['results'])}"
        )
        
        return results


class PerformanceTestMixin:
    """
    Mixin for performance testing.
    """
    
    def time_function(self, func, *args, **kwargs):
        """Time the execution of a function."""
        import time
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        return result, execution_time
    
    def assertExecutionTime(self, max_seconds, func, *args, **kwargs):
        """Assert function executes within time limit."""
        result, execution_time = self.time_function(func, *args, **kwargs)
        
        self.assertLessEqual(
            execution_time, max_seconds,
            f"Function took {execution_time:.3f}s, expected max {max_seconds}s"
        )
        
        return result


# Utility decorators for tests
def with_test_data(dataset='minimal'):
    """
    Decorator to create test data for test methods.
    """
    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            if dataset == 'minimal':
                self.test_data = create_minimal_test_data()
            elif dataset == 'full':
                self.test_data = create_test_dataset()
            else:
                raise ValueError(f"Unknown dataset: {dataset}")
            
            return test_func(self, *args, **kwargs)
        return wrapper
    return decorator


def mock_cache(get_return=None, set_return=True):
    """
    Decorator to mock cache operations.
    """
    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            with patch('django.core.cache.cache.get', return_value=get_return), \
                 patch('django.core.cache.cache.set', return_value=set_return):
                return test_func(self, *args, **kwargs)
        return wrapper
    return decorator


def requires_postgres():
    """
    Decorator to skip tests that require PostgreSQL features.
    """
    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            from django.db import connection
            
            if 'postgresql' not in connection.vendor:
                self.skipTest("This test requires PostgreSQL")
            
            return test_func(self, *args, **kwargs)
        return wrapper
    return decorator


# Custom assertion methods
def assert_model_fields(test_case, instance, expected_fields):
    """Assert that a model instance has expected field values."""
    for field, expected_value in expected_fields.items():
        actual_value = getattr(instance, field)
        test_case.assertEqual(
            actual_value, expected_value,
            f"Field {field}: expected {expected_value}, got {actual_value}"
        )


def assert_serializer_fields(test_case, serializer_data, expected_fields):
    """Assert that serializer data contains expected fields."""
    for field, expected_value in expected_fields.items():
        test_case.assertIn(field, serializer_data)
        if expected_value is not None:
            test_case.assertEqual(serializer_data[field], expected_value)


def assert_api_response_structure(test_case, response_data, expected_structure):
    """Assert that API response has expected structure."""
    def check_structure(data, structure, path=""):
        if isinstance(structure, dict):
            test_case.assertIsInstance(
                data, dict, 
                f"Expected dict at {path}, got {type(data)}"
            )
            for key, value in structure.items():
                test_case.assertIn(key, data, f"Missing key {key} at {path}")
                check_structure(data[key], value, f"{path}.{key}")
        elif isinstance(structure, list):
            test_case.assertIsInstance(
                data, list, 
                f"Expected list at {path}, got {type(data)}"
            )
            if structure and data:
                check_structure(data[0], structure[0], f"{path}[0]")
        elif structure is not None:
            test_case.assertEqual(
                type(data), structure,
                f"Expected {structure} at {path}, got {type(data)}"
            )
    
    check_structure(response_data, expected_structure)