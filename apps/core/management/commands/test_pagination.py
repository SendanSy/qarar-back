"""
Management command to test pagination for hashtags and organizations
"""
from django.core.management.base import BaseCommand
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
import json


class Command(BaseCommand):
    help = 'Test pagination for hashtags and organizations endpoints'
    
    @override_settings(ALLOWED_HOSTS=['testserver', '*'])
    def handle(self, *args, **kwargs):
        client = Client()
        
        self.stdout.write("="*60)
        self.stdout.write("Testing API Pagination")
        self.stdout.write("="*60)
        
        # Test hashtags pagination
        self.test_hashtags_pagination(client)
        
        # Test organizations pagination
        self.test_organizations_pagination(client)
        
        # Test pagination with filters
        self.test_pagination_with_filters(client)
        
        self.stdout.write(self.style.SUCCESS("\nAll pagination tests completed!"))
    
    def test_hashtags_pagination(self, client):
        """Test hashtags endpoint pagination"""
        self.stdout.write("\n" + self.style.NOTICE("Testing Hashtags Pagination"))
        
        # First, check if we have any hashtags
        from apps.content.models.classification import HashTag
        total_hashtags = HashTag.objects.filter(is_active=True).count()
        self.stdout.write(f"Total hashtags in database: {total_hashtags}")
        
        # Test the API endpoint
        response = client.get('/api/v1/content/hashtags/')
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS("✓ Hashtags endpoint working"))
            self.stdout.write(f"  - Total count: {data.get('count', 'N/A')}")
            self.stdout.write(f"  - Page size: {len(data.get('results', []))}")
            self.stdout.write(f"  - Has next page: {'Yes' if data.get('next') else 'No'}")
            
            # Show some hashtags
            if data.get('results'):
                self.stdout.write("\n  Sample hashtags:")
                for i, tag in enumerate(data['results'][:5]):
                    self.stdout.write(f"    {i+1}. #{tag['name']} (posts: {tag.get('post_count', 0)})")
            
            # Test page 2 if available
            if data.get('count', 0) > 20:
                response2 = client.get('/api/v1/content/hashtags/?page=2')
                if response2.status_code == 200:
                    data2 = response2.json()
                    self.stdout.write(self.style.SUCCESS("\n  ✓ Page 2 accessible"))
                    self.stdout.write(f"    - Results on page 2: {len(data2.get('results', []))}")
        else:
            self.stdout.write(self.style.ERROR(f"✗ Error: {response.status_code}"))
    
    def test_organizations_pagination(self, client):
        """Test organizations endpoint pagination"""
        self.stdout.write("\n" + self.style.NOTICE("Testing Organizations Pagination"))
        
        # Check database
        from apps.producers.models import Organization
        total_orgs = Organization.objects.filter(is_active=True).count()
        self.stdout.write(f"Total organizations in database: {total_orgs}")
        
        # Test the API endpoint
        response = client.get('/api/v1/producers/organizations/')
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS("✓ Organizations endpoint working"))
            self.stdout.write(f"  - Total count: {data.get('count', 'N/A')}")
            self.stdout.write(f"  - Page size: {len(data.get('results', []))}")
            self.stdout.write(f"  - Has next page: {'Yes' if data.get('next') else 'No'}")
            
            # Show some organizations
            if data.get('results'):
                self.stdout.write("\n  Sample organizations:")
                for i, org in enumerate(data['results'][:5]):
                    self.stdout.write(f"    {i+1}. {org['name_ar']} ({org['code']})")
            
            # Test different page sizes
            response_small = client.get('/api/v1/producers/organizations/?page_size=5')
            if response_small.status_code == 200:
                data_small = response_small.json()
                self.stdout.write(self.style.SUCCESS("\n  ✓ Custom page size working"))
                self.stdout.write(f"    - Results with page_size=5: {len(data_small.get('results', []))}")
        else:
            self.stdout.write(self.style.ERROR(f"✗ Error: {response.status_code}"))
    
    def test_pagination_with_filters(self, client):
        """Test pagination combined with filters"""
        self.stdout.write("\n" + self.style.NOTICE("Testing Pagination with Filters"))
        
        # Test hashtags with search
        response = client.get('/api/v1/content/hashtags/?search=الجمهورية')
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS("✓ Hashtags search with pagination"))
            self.stdout.write(f"  - Search 'الجمهورية': {data.get('count', 0)} results")
        
        # Test hashtags with ordering
        response = client.get('/api/v1/content/hashtags/?ordering=-post_count')
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                self.stdout.write(self.style.SUCCESS("✓ Hashtags ordering with pagination"))
                top_tag = data['results'][0]
                self.stdout.write(f"  - Top hashtag: #{top_tag['name']} ({top_tag.get('post_count', 0)} posts)")
        
        # Test organizations with search
        response = client.get('/api/v1/producers/organizations/?search=وزارة')
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS("\n✓ Organizations search with pagination"))
            self.stdout.write(f"  - Search 'وزارة': {data.get('count', 0)} results")
        
        # Test pagination info structure
        self.stdout.write("\n" + self.style.NOTICE("Pagination Response Structure:"))
        response = client.get('/api/v1/content/hashtags/?page_size=10')
        if response.status_code == 200:
            data = response.json()
            self.stdout.write("  Expected fields:")
            self.stdout.write(f"    - count: {'✓' if 'count' in data else '✗'}")
            self.stdout.write(f"    - next: {'✓' if 'next' in data else '✗'}")
            self.stdout.write(f"    - previous: {'✓' if 'previous' in data else '✗'}")
            self.stdout.write(f"    - results: {'✓' if 'results' in data else '✗'}")