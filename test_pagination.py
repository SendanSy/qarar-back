#!/usr/bin/env python3
"""
Test script to verify pagination for hashtags and organizations endpoints
"""
import requests
import json

# Base URL - adjust if needed
BASE_URL = "http://localhost:8000/api/v1"

def test_hashtags_pagination():
    """Test hashtags endpoint pagination"""
    print("="*50)
    print("Testing Hashtags Pagination")
    print("="*50)
    
    # Test first page
    url = f"{BASE_URL}/content/hashtags/"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Hashtags endpoint is working")
        print(f"  - Total count: {data.get('count', 'N/A')}")
        print(f"  - Results on page: {len(data.get('results', []))}")
        print(f"  - Next page: {data.get('next', 'None')}")
        print(f"  - Previous page: {data.get('previous', 'None')}")
        
        # Show first few hashtags
        if data.get('results'):
            print("\n  First 3 hashtags:")
            for i, tag in enumerate(data['results'][:3]):
                print(f"    {i+1}. {tag.get('name')} (posts: {tag.get('post_count', 0)})")
        
        # Test second page if available
        if data.get('next'):
            print("\n  Testing page 2...")
            response2 = requests.get(data['next'])
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"  ✓ Page 2 accessible")
                print(f"    - Results on page 2: {len(data2.get('results', []))}")
    else:
        print(f"✗ Error: Status code {response.status_code}")
        print(f"  Response: {response.text}")

def test_organizations_pagination():
    """Test organizations endpoint pagination"""
    print("\n" + "="*50)
    print("Testing Organizations Pagination")
    print("="*50)
    
    # Test first page
    url = f"{BASE_URL}/producers/organizations/"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Organizations endpoint is working")
        print(f"  - Total count: {data.get('count', 'N/A')}")
        print(f"  - Results on page: {len(data.get('results', []))}")
        print(f"  - Next page: {data.get('next', 'None')}")
        print(f"  - Previous page: {data.get('previous', 'None')}")
        
        # Show first few organizations
        if data.get('results'):
            print("\n  First 3 organizations:")
            for i, org in enumerate(data['results'][:3]):
                print(f"    {i+1}. {org.get('name_ar')} ({org.get('code')})")
        
        # Test pagination parameters
        print("\n  Testing custom page size...")
        response_custom = requests.get(f"{url}?page_size=5")
        if response_custom.status_code == 200:
            data_custom = response_custom.json()
            print(f"  ✓ Custom page size working")
            print(f"    - Results with page_size=5: {len(data_custom.get('results', []))}")
    else:
        print(f"✗ Error: Status code {response.status_code}")
        print(f"  Response: {response.text}")

def test_pagination_parameters():
    """Test various pagination parameters"""
    print("\n" + "="*50)
    print("Testing Pagination Parameters")
    print("="*50)
    
    # Test different page numbers
    endpoints = [
        ("Hashtags", f"{BASE_URL}/content/hashtags/"),
        ("Organizations", f"{BASE_URL}/producers/organizations/")
    ]
    
    for name, url in endpoints:
        print(f"\n{name}:")
        
        # Test page parameter
        response = requests.get(f"{url}?page=2")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Page 2: {len(data.get('results', []))} results")
        elif response.status_code == 404:
            print(f"  - Page 2 not found (not enough data)")
        
        # Test ordering with pagination
        if name == "Hashtags":
            response = requests.get(f"{url}?ordering=-post_count")
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    print(f"  ✓ Ordering by post_count (desc): First item has {data['results'][0].get('post_count', 0)} posts")
        
        # Test search with pagination
        response = requests.get(f"{url}?search=a")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Search with 'a': {data.get('count', 0)} total results")

if __name__ == "__main__":
    print("Starting Pagination Tests...")
    print(f"Using base URL: {BASE_URL}\n")
    
    test_hashtags_pagination()
    test_organizations_pagination()
    test_pagination_parameters()
    
    print("\n" + "="*50)
    print("Pagination tests completed!")