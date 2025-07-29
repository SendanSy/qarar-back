"""
Database query optimization and analysis tools.
"""
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.db import connection, models
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from collections import defaultdict
import re
import json

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyze database queries for performance optimization.
    """
    
    def __init__(self):
        self.queries = []
        self.start_time = None
        self.end_time = None
    
    def start_analysis(self):
        """Start query analysis."""
        if settings.DEBUG:
            self.start_time = time.time()
            self.queries = list(connection.queries)
    
    def stop_analysis(self) -> Dict[str, Any]:
        """Stop analysis and return results."""
        if not settings.DEBUG:
            return {'error': 'DEBUG must be enabled for query analysis'}
        
        self.end_time = time.time()
        current_queries = list(connection.queries)
        
        # Get new queries since start
        new_queries = current_queries[len(self.queries):]
        
        return self.analyze_queries(new_queries)
    
    def analyze_queries(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a list of queries and provide optimization insights.
        """
        if not queries:
            return {
                'query_count': 0,
                'total_time': 0,
                'analysis': 'No queries to analyze'
            }
        
        analysis = {
            'query_count': len(queries),
            'total_time': sum(float(q['time']) for q in queries),
            'average_time': sum(float(q['time']) for q in queries) / len(queries),
            'slow_queries': [],
            'duplicate_queries': [],
            'n_plus_one_patterns': [],
            'missing_indexes': [],
            'expensive_operations': [],
            'optimization_suggestions': []
        }
        
        # Analyze individual queries
        query_patterns = defaultdict(list)
        
        for i, query in enumerate(queries):
            sql = query['sql']
            time_taken = float(query['time'])
            
            # Identify slow queries
            if time_taken > 0.1:  # 100ms threshold
                analysis['slow_queries'].append({
                    'index': i,
                    'sql': sql[:200] + '...' if len(sql) > 200 else sql,
                    'time': time_taken,
                    'issues': self._identify_query_issues(sql)
                })
            
            # Group similar queries for duplicate detection
            normalized_sql = self._normalize_query(sql)
            query_patterns[normalized_sql].append({
                'index': i,
                'sql': sql,
                'time': time_taken
            })
        
        # Detect duplicate queries
        for pattern, pattern_queries in query_patterns.items():
            if len(pattern_queries) > 1:
                total_time = sum(q['time'] for q in pattern_queries)
                analysis['duplicate_queries'].append({
                    'pattern': pattern[:100] + '...' if len(pattern) > 100 else pattern,
                    'count': len(pattern_queries),
                    'total_time': total_time,
                    'queries': [q['index'] for q in pattern_queries]
                })
        
        # Detect N+1 patterns
        analysis['n_plus_one_patterns'] = self._detect_n_plus_one(queries)
        
        # Detect missing indexes
        analysis['missing_indexes'] = self._detect_missing_indexes(queries)
        
        # Detect expensive operations
        analysis['expensive_operations'] = self._detect_expensive_operations(queries)
        
        # Generate optimization suggestions
        analysis['optimization_suggestions'] = self._generate_suggestions(analysis)
        
        return analysis
    
    def _normalize_query(self, sql: str) -> str:
        """
        Normalize SQL query for pattern matching.
        """
        # Remove specific values and normalize whitespace
        sql = re.sub(r'\b\d+\b', '?', sql)  # Replace numbers with ?
        sql = re.sub(r"'[^']*'", "'?'", sql)  # Replace string literals
        sql = re.sub(r'"[^"]*"', '"?"', sql)  # Replace quoted identifiers
        sql = re.sub(r'\s+', ' ', sql)  # Normalize whitespace
        return sql.strip().lower()
    
    def _identify_query_issues(self, sql: str) -> List[str]:
        """
        Identify potential issues in a SQL query.
        """
        issues = []
        sql_lower = sql.lower()
        
        # Check for missing WHERE clause
        if 'select' in sql_lower and 'where' not in sql_lower and 'limit' not in sql_lower:
            issues.append('Missing WHERE clause - potential full table scan')
        
        # Check for SELECT *
        if 'select *' in sql_lower:
            issues.append('Using SELECT * - consider selecting specific columns')
        
        # Check for missing LIMIT
        if 'select' in sql_lower and 'limit' not in sql_lower and 'count(' not in sql_lower:
            issues.append('Missing LIMIT clause - potential large result set')
        
        # Check for complex JOINs
        join_count = sql_lower.count(' join ')
        if join_count > 3:
            issues.append(f'Complex query with {join_count} JOINs')
        
        # Check for subqueries
        if '(' in sql and 'select' in sql_lower.split('(')[1:]:
            issues.append('Contains subqueries - consider optimization')
        
        # Check for LIKE with leading wildcard
        if 'like \'%' in sql_lower:
            issues.append('LIKE with leading wildcard - cannot use indexes effectively')
        
        return issues
    
    def _detect_n_plus_one(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect N+1 query patterns.
        """
        patterns = []
        query_groups = defaultdict(list)
        
        # Group queries by normalized pattern
        for i, query in enumerate(queries):
            normalized = self._normalize_query(query['sql'])
            query_groups[normalized].append({
                'index': i,
                'sql': query['sql'],
                'time': float(query['time'])
            })
        
        # Look for patterns with many similar queries
        for pattern, group_queries in query_groups.items():
            if len(group_queries) > 5:  # Threshold for N+1 detection
                total_time = sum(q['time'] for q in group_queries)
                patterns.append({
                    'pattern': pattern[:100] + '...' if len(pattern) > 100 else pattern,
                    'query_count': len(group_queries),
                    'total_time': total_time,
                    'average_time': total_time / len(group_queries),
                    'suggestion': 'Consider using select_related() or prefetch_related()'
                })
        
        return patterns
    
    def _detect_missing_indexes(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect potential missing indexes.
        """
        missing_indexes = []
        
        for query in queries:
            sql = query['sql'].lower()
            time_taken = float(query['time'])
            
            # Look for slow queries with WHERE clauses
            if time_taken > 0.05 and 'where' in sql:  # 50ms threshold
                # Extract table and column information
                tables = self._extract_tables(sql)
                where_columns = self._extract_where_columns(sql)
                
                if tables and where_columns:
                    missing_indexes.append({
                        'sql': query['sql'][:200] + '...' if len(query['sql']) > 200 else query['sql'],
                        'time': time_taken,
                        'tables': tables,
                        'columns': where_columns,
                        'suggestion': f'Consider adding indexes on: {", ".join(where_columns)}'
                    })
        
        return missing_indexes
    
    def _detect_expensive_operations(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect expensive database operations.
        """
        expensive_ops = []
        
        for query in queries:
            sql = query['sql'].lower()
            time_taken = float(query['time'])
            
            operations = []
            
            # Check for expensive operations
            if 'order by' in sql and 'limit' not in sql:
                operations.append('ORDER BY without LIMIT')
            
            if 'group by' in sql and time_taken > 0.1:
                operations.append('Slow GROUP BY operation')
            
            if 'distinct' in sql and time_taken > 0.1:
                operations.append('Slow DISTINCT operation')
            
            if 'like' in sql and time_taken > 0.05:
                operations.append('Slow LIKE operation')
            
            if operations:
                expensive_ops.append({
                    'sql': query['sql'][:200] + '...' if len(query['sql']) > 200 else query['sql'],
                    'time': time_taken,
                    'operations': operations
                })
        
        return expensive_ops
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL."""
        # Simple regex to extract table names
        table_pattern = r'from\s+["`]?(\w+)["`]?'
        matches = re.findall(table_pattern, sql, re.IGNORECASE)
        return matches
    
    def _extract_where_columns(self, sql: str) -> List[str]:
        """Extract column names from WHERE clause."""
        # Simple regex to extract column names from WHERE
        where_pattern = r'where.*?["`]?(\w+)["`]?\s*[=<>!]'
        matches = re.findall(where_pattern, sql, re.IGNORECASE)
        return matches
    
    def _generate_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate optimization suggestions based on analysis.
        """
        suggestions = []
        
        # Suggestions based on slow queries
        if analysis['slow_queries']:
            suggestions.append(f"Found {len(analysis['slow_queries'])} slow queries. Review and optimize.")
        
        # Suggestions based on duplicates
        if analysis['duplicate_queries']:
            suggestions.append("Detected duplicate queries. Consider caching or query optimization.")
        
        # Suggestions based on N+1 patterns
        if analysis['n_plus_one_patterns']:
            suggestions.append("Detected N+1 query patterns. Use select_related() or prefetch_related().")
        
        # Suggestions based on missing indexes
        if analysis['missing_indexes']:
            suggestions.append("Potential missing indexes detected. Consider adding database indexes.")
        
        # General suggestions
        if analysis['query_count'] > 50:
            suggestions.append("High query count detected. Consider query optimization and caching.")
        
        if analysis['total_time'] > 1.0:
            suggestions.append("Total query time is high. Review database performance.")
        
        return suggestions


class QueryProfiler:
    """
    Profile Django ORM queries with context.
    """
    
    def __init__(self, name: str = "Query Profile"):
        self.name = name
        self.analyzer = QueryAnalyzer()
    
    def __enter__(self):
        self.analyzer.start_analysis()
        return self.analyzer
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        analysis = self.analyzer.stop_analysis()
        
        if analysis.get('query_count', 0) > 0:
            logger.info(f"Query Profile '{self.name}': {analysis}")
            
            # Log warnings for performance issues
            if analysis['query_count'] > 20:
                logger.warning(f"High query count in '{self.name}': {analysis['query_count']} queries")
            
            if analysis['total_time'] > 0.5:
                logger.warning(f"Slow query execution in '{self.name}': {analysis['total_time']:.3f}s")


class DatabaseOptimizer:
    """
    Provide database optimization recommendations.
    """
    
    @staticmethod
    def analyze_model_queries(model_class) -> Dict[str, Any]:
        """
        Analyze queries for a specific model.
        """
        with QueryProfiler(f"Model Analysis: {model_class.__name__}") as analyzer:
            # Test common operations
            queryset = model_class.objects.all()
            
            # Test various query patterns
            list(queryset[:10])  # LIMIT query
            queryset.count()     # COUNT query
            
            if hasattr(model_class, 'objects'):
                # Test filtering
                if model_class._meta.fields:
                    first_field = model_class._meta.fields[0]
                    queryset.filter(**{first_field.name + '__isnull': False})[:5]
        
        return analyzer.stop_analysis()
    
    @staticmethod
    def suggest_indexes(model_class) -> List[Dict[str, Any]]:
        """
        Suggest database indexes for a model.
        """
        suggestions = []
        meta = model_class._meta
        
        # Suggest indexes for foreign keys without indexes
        for field in meta.fields:
            if isinstance(field, models.ForeignKey) and not field.db_index:
                suggestions.append({
                    'field': field.name,
                    'type': 'foreign_key',
                    'suggestion': f'Add db_index=True to {field.name}',
                    'impact': 'High - improves JOIN performance'
                })
        
        # Suggest indexes for commonly filtered fields
        common_filter_fields = ['status', 'is_active', 'created_at', 'updated_at']
        for field_name in common_filter_fields:
            try:
                field = meta.get_field(field_name)
                if not field.db_index and field_name != meta.pk.name:
                    suggestions.append({
                        'field': field_name,
                        'type': 'filter_field',
                        'suggestion': f'Consider adding db_index=True to {field_name}',
                        'impact': 'Medium - improves filtering performance'
                    })
            except models.FieldDoesNotExist:
                continue
        
        # Suggest composite indexes for common query patterns
        if hasattr(model_class, 'status') and hasattr(model_class, 'created_at'):
            suggestions.append({
                'fields': ['status', 'created_at'],
                'type': 'composite',
                'suggestion': 'Consider adding composite index on (status, created_at)',
                'impact': 'Medium - improves filtered ordering'
            })
        
        return suggestions
    
    @staticmethod
    def analyze_app_models(app_name: str) -> Dict[str, Any]:
        """
        Analyze all models in an Django app.
        """
        from django.apps import apps
        
        try:
            app_config = apps.get_app_config(app_name)
            models_analysis = {}
            
            for model in app_config.get_models():
                model_name = model.__name__
                models_analysis[model_name] = {
                    'query_analysis': DatabaseOptimizer.analyze_model_queries(model),
                    'index_suggestions': DatabaseOptimizer.suggest_indexes(model),
                    'field_count': len(model._meta.fields),
                    'relationship_count': len([f for f in model._meta.fields 
                                             if isinstance(f, (models.ForeignKey, models.ManyToManyField))])
                }
            
            return models_analysis
            
        except LookupError:
            return {'error': f'App {app_name} not found'}


class QueryOptimizationCommand(BaseCommand):
    """
    Django management command for query optimization analysis.
    """
    help = 'Analyze database queries and provide optimization suggestions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Analyze specific app models'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Analyze specific model'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='console',
            choices=['console', 'json', 'file'],
            help='Output format'
        )
    
    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR('DEBUG must be enabled for query analysis')
            )
            return
        
        app_name = options.get('app')
        model_name = options.get('model')
        output_format = options.get('output')
        
        if model_name:
            # Analyze specific model
            try:
                from django.apps import apps
                model_class = apps.get_model(app_name, model_name)
                analysis = DatabaseOptimizer.analyze_model_queries(model_class)
                suggestions = DatabaseOptimizer.suggest_indexes(model_class)
                
                result = {
                    'model': f"{app_name}.{model_name}",
                    'analysis': analysis,
                    'suggestions': suggestions
                }
                
                self._output_results(result, output_format)
                
            except LookupError:
                self.stdout.write(
                    self.style.ERROR(f'Model {app_name}.{model_name} not found')
                )
        
        elif app_name:
            # Analyze all models in app
            analysis = DatabaseOptimizer.analyze_app_models(app_name)
            self._output_results(analysis, output_format)
        
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --app or --model')
            )
    
    def _output_results(self, results: Dict[str, Any], format: str):
        """Output analysis results in specified format."""
        if format == 'json':
            self.stdout.write(json.dumps(results, indent=2, default=str))
        
        elif format == 'file':
            filename = f'query_analysis_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.stdout.write(
                self.style.SUCCESS(f'Analysis saved to {filename}')
            )
        
        else:  # console
            self._print_console_output(results)
    
    def _print_console_output(self, results: Dict[str, Any]):
        """Print results to console in readable format."""
        self.stdout.write(self.style.SUCCESS('Database Query Analysis Results'))
        self.stdout.write('=' * 50)
        
        for key, value in results.items():
            self.stdout.write(f'\n{self.style.WARNING(key.upper())}:')
            
            if isinstance(value, dict):
                if 'query_count' in value:
                    self.stdout.write(f"  Query Count: {value['query_count']}")
                    self.stdout.write(f"  Total Time: {value.get('total_time', 0):.3f}s")
                    
                    if value.get('slow_queries'):
                        self.stdout.write(f"  Slow Queries: {len(value['slow_queries'])}")
                    
                    if value.get('optimization_suggestions'):
                        self.stdout.write("  Suggestions:")
                        for suggestion in value['optimization_suggestions']:
                            self.stdout.write(f"    - {suggestion}")
            
            self.stdout.write('')


# Utility functions for common optimization tasks
def profile_queryset(queryset, name: str = "Queryset"):
    """Profile a queryset execution."""
    with QueryProfiler(name) as profiler:
        list(queryset)
    return profiler.stop_analysis()


def optimize_queryset(queryset):
    """Automatically optimize a queryset with common patterns."""
    model = queryset.model
    
    # Add select_related for foreign keys
    fk_fields = [f.name for f in model._meta.fields 
                if isinstance(f, models.ForeignKey)]
    if fk_fields:
        queryset = queryset.select_related(*fk_fields)
    
    # Add prefetch_related for reverse foreign keys and M2M
    related_fields = [f.get_accessor_name() for f in model._meta.get_fields() 
                     if f.one_to_many or f.many_to_many]
    if related_fields:
        queryset = queryset.prefetch_related(*related_fields)
    
    return queryset


def suggest_model_optimizations(model_class) -> List[str]:
    """Suggest optimizations for a Django model."""
    suggestions = []
    meta = model_class._meta
    
    # Check for missing indexes
    for field in meta.fields:
        if isinstance(field, models.ForeignKey) and not field.db_index:
            suggestions.append(f"Add db_index=True to {field.name}")
    
    # Check for missing Meta options
    if not getattr(meta, 'ordering', None):
        suggestions.append("Consider adding default ordering in Meta class")
    
    if not getattr(meta, 'indexes', None):
        suggestions.append("Consider adding composite indexes in Meta.indexes")
    
    # Check for model methods that could be optimized
    if hasattr(model_class, '__str__') and not hasattr(model_class, 'select_related'):
        suggestions.append("Consider overriding get_queryset() with select_related() if __str__ accesses related fields")
    
    return suggestions