"""
Test cases for producers app views
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from model_bakery import baker

from apps.producers.models import Organization, Subsidiary, Department
from apps.content.models.post import Post, PostType
from apps.users.models import User
from apps.geographics.models import Country


@pytest.fixture
def api_client():
    """Create an API client"""
    return APIClient()


@pytest.fixture
def country():
    """Create a test country"""
    return baker.make(Country, name='Test Country', code='TC')


@pytest.fixture
def organization(country):
    """Create a test organization"""
    return baker.make(
        Organization,
        name='Test Organization',
        name_ar='منظمة اختبار',
        code='TEST-ORG',
        is_active=True,
        is_verified=True,
        country=country
    )


@pytest.fixture
def subsidiary(organization):
    """Create a test subsidiary"""
    return baker.make(
        Subsidiary,
        name='Test Subsidiary',
        name_ar='فرع اختبار',
        code='TEST-SUB',
        parent_organization=organization,
        is_active=True
    )


@pytest.fixture
def department(subsidiary):
    """Create a test department"""
    return baker.make(
        Department,
        name='Test Department',
        name_ar='قسم اختبار',
        code='TEST-DEPT',
        subsidiary=subsidiary,
        department_type='media',
        employee_count=10,
        is_active=True
    )


@pytest.fixture
def post_type():
    """Create a test post type"""
    return baker.make(PostType, name='News', is_active=True)


@pytest.fixture
def published_post(organization, subsidiary, department, post_type):
    """Create a published post"""
    user = baker.make(User, username='author')
    return baker.make(
        Post,
        title='Test Post',
        organization=organization,
        subsidiary=subsidiary,
        department=department,
        type=post_type,
        author=user,
        status='published'
    )


@pytest.mark.django_db
class TestOrganizationViewSet:
    """Test organization endpoints"""
    
    def test_list_organizations(self, api_client, organization):
        """Test listing organizations"""
        url = reverse('producers:organization-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        
        # Check for count fields
        org_data = response.data['results'][0]
        assert 'subsidiary_count' in org_data
        assert 'department_count' in org_data
    
    def test_retrieve_organization_detail(self, api_client, organization, subsidiary, department):
        """Test retrieving organization detail with nested data"""
        url = reverse('producers:organization-detail', kwargs={'code': organization.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == organization.code
        assert 'subsidiaries' in response.data
        assert len(response.data['subsidiaries']) == 1
        
        # Check nested department data
        sub_data = response.data['subsidiaries'][0]
        assert 'departments' in sub_data
        assert len(sub_data['departments']) == 1
        assert sub_data['departments'][0]['code'] == department.code
    
    def test_organization_posts_endpoint(self, api_client, organization, published_post):
        """Test getting posts for an organization"""
        url = reverse('producers:organization-posts', kwargs={'code': organization.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        assert response.data['results'][0]['title'] == published_post.title
    
    def test_organization_subsidiaries_endpoint(self, api_client, organization, subsidiary):
        """Test getting subsidiaries for an organization"""
        url = reverse('producers:organization-subsidiaries', kwargs={'code': organization.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['code'] == subsidiary.code
    
    def test_organization_departments_endpoint(self, api_client, organization, department):
        """Test getting all departments under an organization"""
        url = reverse('producers:organization-departments', kwargs={'code': organization.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['code'] == department.code
    
    def test_filter_organizations_by_country(self, api_client, organization, country):
        """Test filtering organizations by country"""
        url = reverse('producers:organization-list')
        response = api_client.get(url, {'country': country.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert all(org['country'] == country.id for org in response.data['results'])
    
    def test_search_organizations(self, api_client, organization):
        """Test searching organizations"""
        url = reverse('producers:organization-list')
        response = api_client.get(url, {'search': 'Test'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1


@pytest.mark.django_db
class TestSubsidiaryViewSet:
    """Test subsidiary endpoints"""
    
    def test_list_subsidiaries(self, api_client, subsidiary):
        """Test listing subsidiaries"""
        url = reverse('producers:subsidiary-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
    
    def test_retrieve_subsidiary_detail(self, api_client, subsidiary):
        """Test retrieving subsidiary detail"""
        url = reverse('producers:subsidiary-detail', kwargs={'code': subsidiary.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == subsidiary.code
        assert 'parent_organization_name' in response.data
    
    def test_subsidiary_departments_endpoint(self, api_client, subsidiary, department):
        """Test getting departments for a subsidiary"""
        url = reverse('producers:subsidiary-departments', kwargs={'code': subsidiary.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['code'] == department.code
    
    def test_subsidiary_posts_endpoint(self, api_client, subsidiary, published_post):
        """Test getting posts for a subsidiary"""
        url = reverse('producers:subsidiary-posts', kwargs={'code': subsidiary.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
    
    def test_filter_subsidiaries_by_organization(self, api_client, subsidiary, organization):
        """Test filtering subsidiaries by organization"""
        url = reverse('producers:subsidiary-list')
        response = api_client.get(url, {'organization': organization.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1


@pytest.mark.django_db
class TestDepartmentViewSet:
    """Test department endpoints"""
    
    def test_list_departments(self, api_client, department):
        """Test listing departments"""
        url = reverse('producers:department-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
    
    def test_retrieve_department_detail(self, api_client, department):
        """Test retrieving department detail"""
        url = reverse('producers:department-detail', kwargs={'code': department.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == department.code
        assert response.data['department_type'] == 'media'
        assert 'subsidiary_name' in response.data
        assert 'organization_name' in response.data
    
    def test_department_posts_endpoint(self, api_client, department, published_post):
        """Test getting posts for a department"""
        url = reverse('producers:department-posts', kwargs={'code': department.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
    
    def test_filter_departments_by_type(self, api_client, department):
        """Test filtering departments by type"""
        url = reverse('producers:department-list')
        response = api_client.get(url, {'department_type': 'media'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert all(dept['department_type'] == 'media' for dept in response.data['results'])
    
    def test_filter_departments_by_subsidiary(self, api_client, department, subsidiary):
        """Test filtering departments by subsidiary"""
        url = reverse('producers:department-list')
        response = api_client.get(url, {'subsidiary': subsidiary.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_filter_departments_by_employee_count(self, api_client, department):
        """Test filtering departments by employee count range"""
        url = reverse('producers:department-list')
        response = api_client.get(url, {
            'employee_count_min': 5,
            'employee_count_max': 15
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1


@pytest.mark.django_db
class TestPostFilteringByProducers:
    """Test post filtering by organization/subsidiary/department"""
    
    def test_filter_posts_by_organization(self, api_client, published_post, organization):
        """Test filtering posts by organization"""
        url = reverse('post-list')
        response = api_client.get(url, {'organization': organization.id})
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        # Organization might be returned as an object or ID, so check both
        for post in results:
            if isinstance(post['organization'], dict):
                assert post['organization']['id'] == str(organization.id)
            else:
                assert post['organization'] == organization.id
    
    def test_filter_posts_by_organization_code(self, api_client, published_post, organization):
        """Test filtering posts by organization code"""
        url = reverse('post-list')
        response = api_client.get(url, {'organization_code': organization.code})
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
    
    def test_filter_posts_by_subsidiary(self, api_client, published_post, subsidiary):
        """Test filtering posts by subsidiary"""
        url = reverse('post-list')
        response = api_client.get(url, {'subsidiary': subsidiary.id})
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        # Subsidiary might be returned as an object or ID, so check both
        for post in results:
            if isinstance(post['subsidiary'], dict):
                assert post['subsidiary']['id'] == str(subsidiary.id)
            else:
                assert post['subsidiary'] == subsidiary.id
    
    def test_filter_posts_by_department(self, api_client, published_post, department):
        """Test filtering posts by department"""
        url = reverse('post-list')
        response = api_client.get(url, {'department': department.id})
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        # Department might be returned as an object or ID, so check both
        for post in results:
            if isinstance(post['department'], dict):
                assert post['department']['id'] == str(department.id)
            else:
                assert post['department'] == department.id
    
    def test_filter_posts_by_department_code(self, api_client, published_post, department):
        """Test filtering posts by department code"""
        url = reverse('post-list')
        response = api_client.get(url, {'department_code': department.code})
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1


@pytest.mark.django_db
class TestOrganizationHierarchyData:
    """Test organization hierarchy data in responses"""
    
    def test_organization_list_includes_counts(self, api_client, organization, subsidiary, department):
        """Test organization list includes subsidiary and department counts"""
        # Create another inactive subsidiary
        baker.make(Subsidiary, parent_organization=organization, is_active=False)
        
        url = reverse('producers:organization-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Organization might have integer or string ID
        org_data = None
        for o in response.data['results']:
            if str(o['id']) == str(organization.id) or o['id'] == organization.id:
                org_data = o
                break
        assert org_data is not None
        
        # Should only count active subsidiaries
        assert org_data['subsidiary_count'] == 1
        assert org_data['department_count'] == 1
    
    def test_organization_detail_includes_full_hierarchy(self, api_client, organization):
        """Test organization detail includes full hierarchy"""
        # Create multiple subsidiaries with departments
        sub1 = baker.make(Subsidiary, parent_organization=organization, code='SUB1', is_active=True)
        sub2 = baker.make(Subsidiary, parent_organization=organization, code='SUB2', is_active=True)
        
        dept1 = baker.make(Department, subsidiary=sub1, code='DEPT1', is_active=True)
        dept2 = baker.make(Department, subsidiary=sub1, code='DEPT2', is_active=True)
        dept3 = baker.make(Department, subsidiary=sub2, code='DEPT3', is_active=True)
        
        url = reverse('producers:organization-detail', kwargs={'code': organization.code})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['subsidiaries']) == 2
        
        # Check departments are properly nested
        sub1_data = next(s for s in response.data['subsidiaries'] if s['code'] == 'SUB1')
        assert len(sub1_data['departments']) == 2
        
        sub2_data = next(s for s in response.data['subsidiaries'] if s['code'] == 'SUB2')
        assert len(sub2_data['departments']) == 1