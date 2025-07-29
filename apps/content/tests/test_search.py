"""
Comprehensive tests for search functionality.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.core.test_utils import BaseTestCase, SearchTestMixin, requires_postgres
from apps.core.factories import (
    UserFactory, CategoryFactory, HashTagFactory,
    PostFactory, PublishedPostFactory
)
from apps.core.search import (
    PostSearchService, CategorySearchService, HashTagSearchService,
    UnifiedSearchService, SearchManager
)

User = get_user_model()


class SearchManagerTest(BaseTestCase):
    """Test SearchManager utility functions."""
    
    def test_parse_search_query(self):
        """Test search query parsing."""
        # Test regular query
        query = "django rest framework"
        cleaned, terms = SearchManager.parse_search_query(query)
        
        self.assertEqual(cleaned, "django rest framework")
        self.assertEqual(terms, ["django", "rest", "framework"])
    
    def test_parse_search_query_with_punctuation(self):
        """Test query parsing with punctuation."""
        query = "django, rest & framework!"
        cleaned, terms = SearchManager.parse_search_query(query)
        
        self.assertEqual(cleaned, "django  rest   framework ")
        self.assertIn("django", terms)
        self.assertIn("rest", terms)
        self.assertIn("framework", terms)
    
    def test_parse_search_query_arabic(self):
        """Test query parsing with Arabic text."""
        query = "تطوير المواقع"
        cleaned, terms = SearchManager.parse_search_query(query)
        
        self.assertEqual(cleaned, "تطوير المواقع")
        self.assertEqual(terms, ["تطوير", "المواقع"])
    
    def test_create_search_query(self):
        """Test SearchQuery creation."""
        from django.contrib.postgres.search import SearchQuery
        
        # Test phrase search
        query = SearchManager.create_search_query("test phrase", "phrase")
        self.assertIsInstance(query, SearchQuery)
        
        # Test plain search
        query = SearchManager.create_search_query("test", "plain")
        self.assertIsInstance(query, SearchQuery)


@requires_postgres()
class PostSearchServiceTest(BaseTestCase, SearchTestMixin):
    """Test PostSearchService functionality."""
    
    def setUp(self):
        super().setUp()
        self.service = PostSearchService(self.user)
        self.create_search_test_data()
    
    def test_basic_search(self):
        """Test basic post search functionality."""
        results = self.service.search("Django")
        
        self.assertGreater(results['total_results'], 0)
        self.assertIn('results', results)
        self.assertIn('facets', results)
        self.assertEqual(results['query'], "Django")
    
    def test_search_with_filters(self):
        """Test search with additional filters."""
        category = CategoryFactory()
        post = PublishedPostFactory(title="Filtered Django Post")
        post.categories.add(category)
        
        # Search with category filter
        results = self.service.search(
            "Django",
            filters={'category_id': category.id}
        )
        
        # Should find the filtered post
        post_ids = [p.id for p in results['results']]
        self.assertIn(post.id, post_ids)
    
    def test_search_pagination(self):
        """Test search result pagination."""
        # Create many posts
        for i in range(25):
            PublishedPostFactory(title=f"Django Tutorial {i}")
        
        # Test first page
        page1 = self.service.search("Django", page=1, per_page=10)
        self.assertEqual(len(page1['results']), 10)
        self.assertEqual(page1['page'], 1)
        
        # Test second page
        page2 = self.service.search("Django", page=2, per_page=10)
        self.assertEqual(len(page2['results']), 10)
        self.assertEqual(page2['page'], 2)
        
        # Results should be different
        page1_ids = [p.id for p in page1['results']]
        page2_ids = [p.id for p in page2['results']]
        self.assertEqual(len(set(page1_ids) & set(page2_ids)), 0)
    
    def test_arabic_search(self):
        """Test search with Arabic content."""
        arabic_post = PublishedPostFactory(
            title_ar="تطوير المواقع",
            content_ar="دليل شامل لتطوير مواقع الويب"
        )
        
        results = self.service.search("تطوير")
        
        post_ids = [p.id for p in results['results']]
        self.assertIn(arabic_post.id, post_ids)
    
    def test_search_ranking(self):
        """Test search result ranking."""
        # Create posts with different relevance
        high_relevance = PublishedPostFactory(
            title="Django Tutorial",
            content="This is a comprehensive Django tutorial"
        )
        low_relevance = PublishedPostFactory(
            title="Web Development",
            content="Brief mention of Django framework"
        )
        
        results = self.service.search("Django")
        
        # High relevance post should rank higher
        if len(results['results']) >= 2:
            result_ids = [p.id for p in results['results']]
            high_index = result_ids.index(high_relevance.id)
            low_index = result_ids.index(low_relevance.id)
            self.assertLess(high_index, low_index)
    
    def test_search_highlighting(self):
        """Test search result highlighting."""
        post = PublishedPostFactory(
            title="Django REST Framework",
            content="Learn Django REST Framework development"
        )
        
        results = self.service.search("Django")
        
        # Check if highlighting annotations are present
        for result in results['results']:
            if result.id == post.id:
                self.assertTrue(hasattr(result, 'headline_title'))
                self.assertTrue(hasattr(result, 'headline_content'))
    
    def test_search_facets(self):
        """Test search facet generation."""
        category = CategoryFactory(name="Web Development")
        post_type = PostTypeFactory(name="Tutorial")
        
        post = PublishedPostFactory(title="Django Tutorial", type=post_type)
        post.categories.add(category)
        
        results = self.service.search("Django")
        
        facets = results['facets']
        self.assertIn('categories', facets)
        self.assertIn('post_types', facets)
        self.assertIn('organizations', facets)
    
    def test_search_suggestions(self):
        """Test search suggestions."""
        PublishedPostFactory(title="Django REST Framework Tutorial")
        PublishedPostFactory(title="Django ORM Guide")
        
        results = self.service.search("Djang")  # Typo
        
        suggestions = results['suggestions']
        self.assertIsInstance(suggestions, list)
    
    def test_empty_search(self):
        """Test handling of empty search queries."""
        results = self.service.search("")
        
        self.assertEqual(results['total_results'], 0)
        self.assertEqual(len(results['results']), 0)
    
    def test_search_filters_by_date(self):
        """Test search filtering by date."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create posts from different dates
        recent_date = timezone.now() - timedelta(days=1)
        old_date = timezone.now() - timedelta(days=30)
        
        recent_post = PublishedPostFactory(
            title="Recent Django Post",
            published_at=recent_date
        )
        old_post = PublishedPostFactory(
            title="Old Django Post", 
            published_at=old_date
        )
        
        # Search with date filter
        results = self.service.search(
            "Django",
            filters={'date_from': timezone.now() - timedelta(days=7)}
        )
        
        post_ids = [p.id for p in results['results']]
        self.assertIn(recent_post.id, post_ids)
        self.assertNotIn(old_post.id, post_ids)


class CategorySearchServiceTest(BaseTestCase):
    """Test CategorySearchService functionality."""
    
    def setUp(self):
        super().setUp()
        self.service = CategorySearchService(self.user)
    
    def test_category_search(self):
        """Test basic category search."""
        category1 = CategoryFactory(name="Web Development")
        category2 = CategoryFactory(name="Mobile Development") 
        category3 = CategoryFactory(name="Database Design")
        
        results = self.service.search("Development")
        
        result_ids = [c.id for c in results]
        self.assertIn(category1.id, result_ids)
        self.assertIn(category2.id, result_ids)
        self.assertNotIn(category3.id, result_ids)
    
    def test_category_search_arabic(self):
        """Test category search with Arabic names."""
        category = CategoryFactory(name_ar="تطوير المواقع")
        
        results = self.service.search("تطوير")
        
        result_ids = [c.id for c in results]
        self.assertIn(category.id, result_ids)
    
    def test_category_search_inactive(self):
        """Test that inactive categories are excluded."""
        active_cat = CategoryFactory(name="Active Category", is_active=True)
        inactive_cat = CategoryFactory(name="Inactive Category", is_active=False)
        
        results = self.service.search("Category")
        
        result_ids = [c.id for c in results]
        self.assertIn(active_cat.id, result_ids)
        self.assertNotIn(inactive_cat.id, result_ids)


class HashTagSearchServiceTest(BaseTestCase):
    """Test HashTagSearchService functionality."""
    
    def setUp(self):
        super().setUp()
        self.service = HashTagSearchService(self.user)
    
    def test_hashtag_search(self):
        """Test basic hashtag search."""
        tag1 = HashTagFactory(name="django")
        tag2 = HashTagFactory(name="python")
        tag3 = HashTagFactory(name="javascript")
        
        results = self.service.search("py")
        
        result_names = [t.name for t in results]
        self.assertIn("python", result_names)
        self.assertNotIn("javascript", result_names)
    
    def test_hashtag_search_with_hash(self):
        """Test hashtag search with # prefix."""
        tag = HashTagFactory(name="django")
        
        # Search with # should work
        results = self.service.search("#django")
        
        result_names = [t.name for t in results]
        self.assertIn("django", result_names)
    
    def test_hashtag_search_ordering(self):
        """Test hashtag search result ordering."""
        popular_tag = HashTagFactory(name="python", post_count=100)
        unpopular_tag = HashTagFactory(name="pypy", post_count=1)
        
        results = self.service.search("py")
        
        # Popular tag should come first
        if len(results) >= 2:
            self.assertEqual(results[0], popular_tag)


class UnifiedSearchServiceTest(BaseTestCase, SearchTestMixin):
    """Test UnifiedSearchService functionality."""
    
    def setUp(self):
        super().setUp()
        self.service = UnifiedSearchService(self.user)
        self.create_search_test_data()
    
    def test_unified_search(self):
        """Test unified search across all content types."""
        # Create content for different types
        post = PublishedPostFactory(title="Django Tutorial")
        category = CategoryFactory(name="Django Framework")
        hashtag = HashTagFactory(name="django")
        
        results = self.service.search_all("Django")
        
        # Should have results from all types
        self.assertIn('posts', results)
        self.assertIn('categories', results)
        self.assertIn('hashtags', results)
        
        # Check total results
        self.assertGreater(results['total_results'], 0)
    
    def test_unified_search_with_filters(self):
        """Test unified search with filters."""
        category = CategoryFactory()
        post = PublishedPostFactory(title="Filtered Content")
        post.categories.add(category)
        
        results = self.service.search_all(
            "Content",
            filters={'category_id': category.id}
        )
        
        # Post search should respect filters
        post_results = results['posts']
        self.assertGreater(post_results['total_results'], 0)


class SearchPerformanceTest(BaseTestCase, SearchTestMixin):
    """Test search performance and optimization."""
    
    def setUp(self):
        super().setUp()
        self.service = PostSearchService(self.user)
        
        # Create large dataset for performance testing
        self.categories = CategoryFactory.create_batch(10)
        self.hashtags = HashTagFactory.create_batch(20)
        
        # Create many posts
        for i in range(100):
            post = PublishedPostFactory(
                title=f"Performance Test Post {i}",
                content=f"Content for performance testing with keyword {i}"
            )
            # Add random categories and hashtags
            post.categories.add(self.categories[i % len(self.categories)])
            post.hashtags.add(self.hashtags[i % len(self.hashtags)])
    
    def test_search_performance(self):
        """Test that search performs within acceptable time limits."""
        from apps.core.test_utils import PerformanceTestMixin
        
        class TestClass(PerformanceTestMixin):
            def search_operation(self):
                return self.service.search("Performance", per_page=20)
        
        test_instance = TestClass()
        test_instance.service = self.service
        
        # Search should complete within 2 seconds
        result = test_instance.assertExecutionTime(2.0, test_instance.search_operation)
        
        self.assertGreater(result['total_results'], 0)
    
    def test_search_query_count(self):
        """Test that search doesn't generate too many database queries."""
        from apps.core.test_utils import DatabaseTestMixin
        
        class TestClass(DatabaseTestMixin):
            pass
        
        test_instance = TestClass()
        
        # Search should use reasonable number of queries
        def search_func():
            return self.service.search("Performance", per_page=20)
        
        test_instance.assertMaxQueryCount(10, search_func)
    
    def test_search_caching(self):
        """Test that search results are cached."""
        from unittest.mock import patch
        
        query = "Performance Test"
        
        # First search should hit database
        with patch('apps.core.cache.CacheManager.get', return_value=None) as mock_get, \
             patch('apps.core.cache.CacheManager.set') as mock_set:
            
            result1 = self.service.search(query)
            
            # Should try to get from cache
            mock_get.assert_called()
            # Should cache the result
            mock_set.assert_called()
        
        # Second search should use cache
        with patch('apps.core.cache.CacheManager.get', return_value=result1) as mock_get:
            result2 = self.service.search(query)
            
            # Should get from cache
            mock_get.assert_called()
            self.assertEqual(result2, result1)