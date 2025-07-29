"""
Advanced search functionality with PostgreSQL full-text search.
"""
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, SearchHeadline,
    TrigramSimilarity
)
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Q, F, Count, Case, When, Value, TextField
from django.db.models.functions import Greatest, Coalesce
from django.utils import timezone
from typing import Dict, List, Any, Optional, Tuple
import re

from apps.core.cache import CacheManager, cache_result
from apps.core.services import BaseService


class SearchManager:
    """
    Centralized search management with caching and analytics.
    """
    
    @staticmethod
    def build_search_vector(model_class, fields: Dict[str, str]) -> SearchVector:
        """
        Build a search vector from multiple fields with weights.
        
        Args:
            model_class: The Django model class
            fields: Dict mapping field names to weights ('A', 'B', 'C', 'D')
        """
        vectors = []
        for field, weight in fields.items():
            if hasattr(model_class, field):
                vectors.append(SearchVector(field, weight=weight))
        
        if vectors:
            return vectors[0] if len(vectors) == 1 else sum(vectors[1:], vectors[0])
        return SearchVector('id')  # Fallback
    
    @staticmethod
    def parse_search_query(query: str) -> Tuple[str, List[str]]:
        """
        Parse search query and extract terms.
        
        Returns:
            Tuple of (cleaned_query, individual_terms)
        """
        # Clean the query
        cleaned = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', query).strip()
        
        # Extract terms
        terms = [term.strip() for term in cleaned.split() if len(term.strip()) > 1]
        
        return cleaned, terms
    
    @staticmethod
    def create_search_query(query: str, search_type: str = 'phrase') -> SearchQuery:
        """
        Create a SearchQuery object with proper configuration.
        
        Args:
            query: The search query string
            search_type: 'phrase', 'plain', or 'raw'
        """
        if search_type == 'phrase':
            return SearchQuery(query, search_type='phrase')
        elif search_type == 'raw':
            return SearchQuery(query, search_type='raw')
        else:
            return SearchQuery(query, search_type='plain')


class PostSearchService(BaseService):
    """
    Advanced search service for posts with full-text search capabilities.
    """
    
    # Search field weights (A=1.0, B=0.4, C=0.2, D=0.1)
    SEARCH_FIELDS = {
        'title': 'A',
        'title_ar': 'A', 
        'summary': 'B',
        'summary_ar': 'B',
        'content': 'C',
        'content_ar': 'C',
        'meta_keywords': 'D',
    }
    
    def __init__(self, user: Optional[Any] = None):
        super().__init__(user)
        from apps.content.models.post import Post
        self.model = Post
    
    def search(self, query: str, filters: Dict[str, Any] = None, 
              page: int = 1, per_page: int = 20, search_type: str = 'phrase') -> Dict[str, Any]:
        """
        Perform advanced full-text search with ranking and highlighting.
        """
        if not query or len(query.strip()) < 2:
            return self._empty_search_result()
        
        # Parse and clean query
        cleaned_query, terms = SearchManager.parse_search_query(query)
        
        # Check cache
        cache_key = f"search_{hash(query)}_{hash(str(filters))}_{page}_{per_page}"
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build base queryset
        queryset = self._get_search_queryset(filters)
        
        # Apply search
        search_result = self._perform_search(
            queryset, cleaned_query, terms, search_type, page, per_page
        )
        
        # Add analytics
        self._track_search(query, search_result['total_results'])
        
        # Cache result
        CacheManager.set(cache_key, search_result, 'short')
        
        return search_result
    
    def _get_search_queryset(self, filters: Dict[str, Any] = None):
        """Get base queryset for search with optimizations."""
        queryset = self.model.objects.published().select_related(
            'author', 'type', 'organization', 'subsidiary'
        ).prefetch_related('categories', 'hashtags')
        
        # Apply filters
        if filters:
            if 'category_id' in filters:
                queryset = queryset.filter(categories__id=filters['category_id'])
            
            if 'post_type_id' in filters:
                queryset = queryset.filter(type_id=filters['post_type_id'])
            
            if 'organization_id' in filters:
                queryset = queryset.filter(organization_id=filters['organization_id'])
            
            if 'date_from' in filters:
                queryset = queryset.filter(published_at__gte=filters['date_from'])
            
            if 'date_to' in filters:
                queryset = queryset.filter(published_at__lte=filters['date_to'])
            
            if 'is_featured' in filters:
                queryset = queryset.filter(is_featured=filters['is_featured'])
            
            if 'language' in filters:
                queryset = queryset.filter(language_code=filters['language'])
        
        return queryset
    
    def _perform_search(self, queryset, query: str, terms: List[str], 
                       search_type: str, page: int, per_page: int) -> Dict[str, Any]:
        """Perform the actual search with ranking and highlighting."""
        
        # Build search vector
        search_vector = SearchManager.build_search_vector(self.model, self.SEARCH_FIELDS)
        
        # Create search queries
        main_query = SearchManager.create_search_query(query, search_type)
        
        # For better results, also try individual terms
        term_queries = [
            SearchManager.create_search_query(term, 'plain') for term in terms
        ]
        
        # Apply search with ranking
        search_queryset = queryset.annotate(
            search_vector=search_vector,
            rank=SearchRank(search_vector, main_query),
            # Add trigram similarity for better fuzzy matching
            similarity=Greatest(
                TrigramSimilarity('title', query),
                TrigramSimilarity('title_ar', query),
                TrigramSimilarity('summary', query),
                TrigramSimilarity('summary_ar', query)
            )
        )
        
        # Build the filter query properly
        filter_query = Q(search_vector=main_query) | Q(similarity__gte=0.3)
        for tq in term_queries:
            filter_query |= Q(search_vector=tq)
        
        search_queryset = search_queryset.filter(filter_query).distinct()
        
        # Order by relevance
        search_queryset = search_queryset.order_by(
            '-rank', '-similarity', '-view_count', '-published_at'
        )
        
        # Add highlighting
        search_queryset = search_queryset.annotate(
            headline_title=SearchHeadline(
                'title',
                main_query,
                start_sel='<mark>',
                stop_sel='</mark>',
                max_words=10
            ),
            headline_title_ar=SearchHeadline(
                'title_ar',
                main_query,
                start_sel='<mark>',
                stop_sel='</mark>',
                max_words=10
            ),
            headline_content=SearchHeadline(
                'content',
                main_query,
                start_sel='<mark>',
                stop_sel='</mark>',
                max_words=50
            )
        )
        
        # Count total results
        total_results = search_queryset.count()
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        results = list(search_queryset[start:end])
        
        # Build facets for filtering
        facets = self._build_search_facets(queryset, query, main_query)
        
        return {
            'query': query,
            'total_results': total_results,
            'page': page,
            'per_page': per_page,
            'results': results,
            'facets': facets,
            'suggestions': self._get_search_suggestions(query, terms)
        }
    
    def _build_search_facets(self, base_queryset, query: str, search_query) -> Dict[str, Any]:
        """Build search facets for filtering."""
        
        # Get search results for facet calculation
        search_vector = SearchManager.build_search_vector(self.model, self.SEARCH_FIELDS)
        facet_queryset = base_queryset.annotate(
            search_vector=search_vector
        ).filter(search_vector=search_query)
        
        # Category facets
        category_facets = list(
            facet_queryset.values('categories__name', 'categories__id')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Post type facets
        type_facets = list(
            facet_queryset.values('type__name', 'type__id')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Organization facets
        org_facets = list(
            facet_queryset.values('organization__name', 'organization__id')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Date facets (by month)
        date_facets = list(
            facet_queryset.extra(
                select={'month': "DATE_TRUNC('month', published_at)"}
            ).values('month')
            .annotate(count=Count('id'))
            .order_by('-month')[:12]
        )
        
        return {
            'categories': category_facets,
            'post_types': type_facets,
            'organizations': org_facets,
            'dates': date_facets
        }
    
    def _get_search_suggestions(self, query: str, terms: List[str]) -> List[str]:
        """Get search suggestions based on popular searches and content."""
        suggestions = []
        
        # Get similar searches from analytics (if implemented)
        # For now, return trigram-based suggestions from titles
        if len(query) >= 3:
            similar_titles = self.model.objects.published().annotate(
                similarity=Greatest(
                    TrigramSimilarity('title', query),
                    TrigramSimilarity('title_ar', query)
                )
            ).filter(similarity__gte=0.2).order_by('-similarity')[:5]
            
            suggestions.extend([
                post.title for post in similar_titles 
                if post.title and post.title.lower() != query.lower()
            ])
        
        return suggestions[:5]
    
    def _empty_search_result(self) -> Dict[str, Any]:
        """Return empty search result structure."""
        return {
            'query': '',
            'total_results': 0,
            'page': 1,
            'per_page': 20,
            'results': [],
            'facets': {},
            'suggestions': []
        }
    
    def _track_search(self, query: str, results_count: int) -> None:
        """Track search analytics."""
        try:
            # Store search analytics
            from apps.content.models.analytics import SearchAnalytics
            SearchAnalytics.objects.create(
                query=query,
                results_count=results_count,
                user=self.user if self.user and self.user.is_authenticated else None,
                timestamp=timezone.now()
            )
        except ImportError:
            # SearchAnalytics model doesn't exist yet
            self._log_action('search', details={
                'query': query,
                'results_count': results_count
            })
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search queries."""
        cache_key = f"popular_searches_{limit}"
        popular = CacheManager.get(cache_key)
        
        if popular is None:
            try:
                from apps.content.models.analytics import SearchAnalytics
                
                # Get popular searches from last 30 days
                cutoff_date = timezone.now() - timezone.timedelta(days=30)
                popular = list(
                    SearchAnalytics.objects.filter(
                        timestamp__gte=cutoff_date,
                        results_count__gt=0
                    ).values('query')
                    .annotate(search_count=Count('id'))
                    .order_by('-search_count')[:limit]
                )
                
                CacheManager.set(cache_key, popular, 'long')
            except ImportError:
                popular = []
        
        return popular
    
    def autocomplete(self, query: str, limit: int = 10) -> List[str]:
        """Provide autocomplete suggestions."""
        if len(query) < 2:
            return []
        
        cache_key = f"autocomplete_{query}_{limit}"
        suggestions = CacheManager.get(cache_key)
        
        if suggestions is None:
            # Get suggestions from post titles
            title_suggestions = self.model.objects.published().filter(
                Q(title__icontains=query) | Q(title_ar__icontains=query)
            ).values_list('title', 'title_ar').distinct()[:limit]
            
            suggestions = []
            for title, title_ar in title_suggestions:
                if title and query.lower() in title.lower():
                    suggestions.append(title)
                elif title_ar and query in title_ar:
                    suggestions.append(title_ar)
            
            # Remove duplicates and limit
            suggestions = list(set(suggestions))[:limit]
            
            CacheManager.set(cache_key, suggestions, 'medium')
        
        return suggestions


class CategorySearchService(BaseService):
    """
    Search service for categories.
    """
    
    def __init__(self, user: Optional[Any] = None):
        super().__init__(user)
        from apps.content.models.classification import Category
        self.model = Category
    
    def search(self, query: str, limit: int = 10) -> List[Any]:
        """Search categories by name."""
        if not query or len(query.strip()) < 2:
            return []
        
        cache_key = f"category_search_{query}_{limit}"
        results = CacheManager.get(cache_key)
        
        if results is None:
            queryset = self.model.objects.filter(
                is_deleted=False,
                is_active=True
            ).annotate(
                similarity=Greatest(
                    TrigramSimilarity('name', query),
                    TrigramSimilarity('name_ar', query)
                )
            ).filter(
                Q(name__icontains=query) |
                Q(name_ar__icontains=query) |
                Q(similarity__gte=0.3)
            ).order_by('-similarity', 'name')
            
            results = list(queryset[:limit])
            CacheManager.set(cache_key, results, 'medium')
        
        return results


class HashTagSearchService(BaseService):
    """
    Search service for hashtags.
    """
    
    def __init__(self, user: Optional[Any] = None):
        super().__init__(user)
        from apps.content.models.classification import HashTag
        self.model = HashTag
    
    def search(self, query: str, limit: int = 10) -> List[Any]:
        """Search hashtags by name."""
        if not query or len(query.strip()) < 2:
            return []
        
        # Remove # if present
        clean_query = query.lstrip('#')
        
        cache_key = f"hashtag_search_{clean_query}_{limit}"
        results = CacheManager.get(cache_key)
        
        if results is None:
            results = list(
                self.model.objects.filter(
                    is_deleted=False,
                    is_active=True,
                    name__icontains=clean_query
                ).order_by('-post_count', 'name')[:limit]
            )
            CacheManager.set(cache_key, results, 'medium')
        
        return results


class UnifiedSearchService(BaseService):
    """
    Unified search service that searches across all content types.
    """
    
    def __init__(self, user: Optional[Any] = None):
        super().__init__(user)
        self.post_search = PostSearchService(user)
        self.category_search = CategorySearchService(user)
        self.hashtag_search = HashTagSearchService(user)
    
    def search_all(self, query: str, filters: Dict[str, Any] = None,
                  page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search across all content types.
        """
        # Main post search
        post_results = self.post_search.search(
            query, filters, page, per_page
        )
        
        # Quick searches for other types
        categories = self.category_search.search(query, limit=5)
        hashtags = self.hashtag_search.search(query, limit=5)
        
        return {
            'query': query,
            'posts': post_results,
            'categories': categories,
            'hashtags': hashtags,
            'total_results': (
                post_results['total_results'] + 
                len(categories) + 
                len(hashtags)
            )
        }