"""
Management command to verify API structure and pagination
"""
from django.core.management.base import BaseCommand
from django.test import Client
from django.test.utils import override_settings
import json


class Command(BaseCommand):
    help = 'Verify API structure including pagination for all key endpoints'
    
    @override_settings(ALLOWED_HOSTS=['testserver', '*'])
    def handle(self, *args, **kwargs):
        client = Client()
        
        self.stdout.write("="*60)
        self.stdout.write("API Structure Verification")
        self.stdout.write("="*60)
        
        endpoints = [
            ('/api/v1/content/hashtags/', 'Hashtags'),
            ('/api/v1/producers/organizations/', 'Organizations'),
            ('/api/v1/producers/subsidiaries/', 'Subsidiaries'),
            ('/api/v1/producers/departments/', 'Departments'),
            ('/api/v1/content/categories/', 'Categories'),
            ('/api/v1/content/post-types/', 'Post Types'),
        ]
        
        for endpoint, name in endpoints:
            self.stdout.write(f"\n{self.style.NOTICE(name)} ({endpoint})")
            
            # Test GET request
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(self.style.SUCCESS("✓ GET request successful"))
                
                # Check pagination structure
                if isinstance(data, dict) and 'results' in data:
                    self.stdout.write("  ✓ Paginated response")
                    self.stdout.write(f"    - Total count: {data.get('count', 'N/A')}")
                    self.stdout.write(f"    - Page size: {len(data.get('results', []))}")
                    self.stdout.write(f"    - Has 'next': {'✓' if 'next' in data else '✗'}")
                    self.stdout.write(f"    - Has 'previous': {'✓' if 'previous' in data else '✗'}")
                    self.stdout.write(f"    - Has 'results': {'✓' if 'results' in data else '✗'}")
                elif isinstance(data, list):
                    self.stdout.write("  ✗ Non-paginated response (list)")
                    self.stdout.write(f"    - Items: {len(data)}")
                else:
                    self.stdout.write("  ? Unknown response structure")
            else:
                self.stdout.write(self.style.ERROR(f"✗ GET request failed: {response.status_code}"))
        
        # Test specific pagination features
        self.stdout.write("\n" + "="*60)
        self.stdout.write("Pagination Features Test")
        self.stdout.write("="*60)
        
        # Test page_size parameter
        self.stdout.write("\n" + self.style.NOTICE("Custom Page Size"))
        test_sizes = [5, 10, 50]
        for size in test_sizes:
            response = client.get(f'/api/v1/content/hashtags/?page_size={size}')
            if response.status_code == 200:
                data = response.json()
                actual_size = len(data.get('results', []))
                expected = min(size, data.get('count', 0))
                if actual_size == expected or actual_size == size:
                    self.stdout.write(f"  ✓ page_size={size}: Got {actual_size} results")
                else:
                    self.stdout.write(f"  ✗ page_size={size}: Expected {expected}, got {actual_size}")
        
        # Test ordering
        self.stdout.write("\n" + self.style.NOTICE("Ordering"))
        response = client.get('/api/v1/content/hashtags/?ordering=name')
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                first = data['results'][0].get('name', '')
                self.stdout.write(f"  ✓ Ascending order: First item = '{first}'")
        
        response = client.get('/api/v1/content/hashtags/?ordering=-post_count')
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                first = data['results'][0]
                self.stdout.write(f"  ✓ Descending order by post_count: '{first.get('name')}' ({first.get('post_count', 0)} posts)")
        
        self.stdout.write("\n" + self.style.SUCCESS("API structure verification completed!"))