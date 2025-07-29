"""
Performance monitoring and logging utilities for the Qarar project.
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, List
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.http import HttpRequest, HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
import json
import traceback

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitor and log API performance metrics.
    """
    
    @staticmethod
    def log_api_call(request: Request, response: Response, execution_time: float,
                    query_count: int = None, cache_hits: int = None) -> None:
        """
        Log API call performance metrics.
        """
        user_id = request.user.id if request.user.is_authenticated else None
        
        log_data = {
            'method': request.method,
            'path': request.path,
            'user_id': user_id,
            'status_code': response.status_code,
            'execution_time_ms': round(execution_time * 1000, 2),
            'query_count': query_count,
            'cache_hits': cache_hits,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': PerformanceMonitor._get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Add request size if available
        if hasattr(request, 'body'):
            log_data['request_size'] = len(request.body)
        
        # Add response size
        if hasattr(response, 'content'):
            log_data['response_size'] = len(response.content)
        
        # Log warnings for slow requests
        if execution_time > 1.0:  # More than 1 second
            logger.warning(f"Slow API call: {log_data}")
        elif execution_time > 0.5:  # More than 500ms
            logger.info(f"Moderate API call: {log_data}")
        else:
            logger.debug(f"Fast API call: {log_data}")
    
    @staticmethod
    def log_database_queries(queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Log and analyze database query performance.
        """
        if not queries:
            return {'query_count': 0, 'total_time': 0}
        
        total_time = sum(float(q['time']) for q in queries)
        slow_queries = [q for q in queries if float(q['time']) > 0.1]  # > 100ms
        
        query_stats = {
            'query_count': len(queries),
            'total_time_ms': round(total_time * 1000, 2),
            'slow_query_count': len(slow_queries),
            'average_time_ms': round((total_time / len(queries)) * 1000, 2),
        }
        
        if slow_queries:
            logger.warning(f"Slow database queries detected: {query_stats}")
            for i, query in enumerate(slow_queries[:5]):  # Log first 5 slow queries
                logger.warning(f"Slow query {i+1}: {query['sql'][:200]}... (Time: {query['time']}s)")
        
        return query_stats
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'


class QueryCountLogger:
    """
    Context manager to track database queries.
    """
    
    def __init__(self):
        self.initial_queries = 0
        self.final_queries = 0
        self.queries = []
    
    def __enter__(self):
        if settings.DEBUG:
            self.initial_queries = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if settings.DEBUG:
            self.final_queries = len(connection.queries)
            self.queries = connection.queries[self.initial_queries:self.final_queries]
    
    @property
    def query_count(self) -> int:
        """Get the number of queries executed."""
        return self.final_queries - self.initial_queries
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get detailed query statistics."""
        return PerformanceMonitor.log_database_queries(self.queries)


class CacheMonitor:
    """
    Monitor cache hit/miss ratios.
    """
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.operations = []
    
    def record_hit(self, key: str):
        """Record a cache hit."""
        self.hits += 1
        self.operations.append({'type': 'hit', 'key': key, 'timestamp': time.time()})
    
    def record_miss(self, key: str):
        """Record a cache miss."""
        self.misses += 1
        self.operations.append({'type': 'miss', 'key': key, 'timestamp': time.time()})
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_ratio': round(self.hit_ratio, 3),
            'total_operations': self.hits + self.misses
        }


def monitor_performance(track_queries: bool = True, track_cache: bool = True):
    """
    Decorator to monitor function performance.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Initialize monitors
            query_logger = QueryCountLogger() if track_queries else None
            cache_monitor = CacheMonitor() if track_cache else None
            
            try:
                with query_logger if query_logger else nullcontext():
                    result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                
                # Log performance metrics
                log_data = {
                    'function': f"{func.__module__}.{func.__name__}",
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()),
                }
                
                if query_logger:
                    query_stats = query_logger.get_query_stats()
                    log_data.update(query_stats)
                
                if cache_monitor:
                    cache_stats = cache_monitor.get_stats()
                    log_data.update(cache_stats)
                
                # Log based on performance
                if execution_time > 2.0:
                    logger.error(f"Very slow function: {log_data}")
                elif execution_time > 1.0:
                    logger.warning(f"Slow function: {log_data}")
                elif execution_time > 0.5:
                    logger.info(f"Moderate function: {log_data}")
                else:
                    logger.debug(f"Fast function: {log_data}")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Function error: {func.__name__} failed after {execution_time:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


class APIPerformanceMiddleware:
    """
    Middleware to monitor API performance.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Track queries if DEBUG is enabled
        query_logger = QueryCountLogger() if settings.DEBUG else None
        
        with query_logger if query_logger else nullcontext():
            response = self.get_response(request)
        
        execution_time = time.time() - start_time
        
        # Log performance for API endpoints
        if request.path.startswith('/api/'):
            query_count = query_logger.query_count if query_logger else None
            
            PerformanceMonitor.log_api_call(
                request=request,
                response=response,
                execution_time=execution_time,
                query_count=query_count
            )
        
        # Add performance headers
        response['X-Response-Time'] = f"{execution_time:.3f}s"
        if query_logger:
            response['X-DB-Queries'] = str(query_logger.query_count)
        
        return response


class HealthCheckMonitor:
    """
    Monitor application health metrics.
    """
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Simple query to check DB
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2),
                'connection_count': len(connection.queries) if settings.DEBUG else None
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def check_cache() -> Dict[str, Any]:
        """Check cache connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test cache operations
            test_key = 'health_check_test'
            test_value = 'test_value'
            
            cache.set(test_key, test_value, 10)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            response_time = time.time() - start_time
            
            if retrieved_value == test_value:
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time * 1000, 2)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Cache value mismatch'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def check_search() -> Dict[str, Any]:
        """Check search functionality."""
        try:
            start_time = time.time()
            
            # Test basic search
            from apps.core.search import PostSearchService
            search_service = PostSearchService()
            results = search_service.search("test", per_page=1)
            
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2),
                'results_count': results['total_results']
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get system performance metrics."""
        import psutil
        import os
        
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process(os.getpid())
            
            return {
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent_used': memory.percent
                },
                'cpu': {
                    'percent_used': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent_used': round((disk.used / disk.total) * 100, 2)
                },
                'process': {
                    'memory_mb': round(process.memory_info().rss / (1024**2), 2),
                    'cpu_percent': process.cpu_percent(),
                    'threads': process.num_threads()
                }
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}


class ErrorTracker:
    """
    Track and log application errors.
    """
    
    @staticmethod
    def log_error(request: HttpRequest, exception: Exception, 
                 context: Dict[str, Any] = None) -> None:
        """
        Log detailed error information.
        """
        error_data = {
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'path': request.path,
            'method': request.method,
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            'ip_address': PerformanceMonitor._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': timezone.now().isoformat(),
            'traceback': traceback.format_exc(),
        }
        
        if context:
            error_data['context'] = context
        
        # Add request data (be careful with sensitive data)
        if request.method == 'POST':
            # Don't log sensitive data like passwords
            post_data = dict(request.POST)
            sensitive_fields = ['password', 'token', 'secret', 'key']
            for field in sensitive_fields:
                if field in post_data:
                    post_data[field] = '[REDACTED]'
            error_data['post_data'] = post_data
        
        logger.error(f"Application error: {error_data}")
    
    @staticmethod
    def log_api_error(request: Request, exception: Exception,
                     response_data: Dict[str, Any] = None) -> None:
        """
        Log API-specific errors.
        """
        error_data = {
            'api_error': True,
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'endpoint': request.path,
            'method': request.method,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'timestamp': timezone.now().isoformat(),
        }
        
        if response_data:
            error_data['response_data'] = response_data
        
        logger.error(f"API error: {error_data}")


# Context manager for null contexts (Python < 3.7 compatibility)
class nullcontext:
    """A context manager that does nothing."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    def __enter__(self):
        return self.return_value
    
    def __exit__(self, *excinfo):
        pass


# Utility functions for common monitoring tasks
def time_function(func, *args, **kwargs):
    """Time the execution of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    return result, execution_time


def log_slow_query_warning(queryset, threshold_ms: int = 100):
    """Log warning if queryset execution is slow."""
    def execute_and_log():
        start_time = time.time()
        result = list(queryset)
        execution_time = (time.time() - start_time) * 1000
        
        if execution_time > threshold_ms:
            logger.warning(f"Slow queryset execution: {execution_time:.2f}ms")
        
        return result
    
    return execute_and_log()


def track_user_action(user, action: str, resource_type: str = None,
                     resource_id: str = None, metadata: Dict[str, Any] = None):
    """Track user actions for analytics."""
    action_data = {
        'user_id': user.id if user and user.is_authenticated else None,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'metadata': metadata or {},
        'timestamp': timezone.now().isoformat(),
    }
    
    logger.info(f"User action: {action_data}")
    
    # Store in database if analytics model exists
    try:
        from apps.analytics.models import UserAction
        UserAction.objects.create(**action_data)
    except ImportError:
        # Analytics app not available
        pass