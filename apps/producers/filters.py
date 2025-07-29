"""
Filters for producers app
"""
import django_filters
from .models import Organization, Subsidiary, Department


class OrganizationFilter(django_filters.FilterSet):
    """Filter for Organization"""
    is_verified = django_filters.BooleanFilter()
    country = django_filters.NumberFilter(field_name='country__id')
    state = django_filters.NumberFilter(field_name='state__id')
    city = django_filters.NumberFilter(field_name='city__id')
    
    class Meta:
        model = Organization
        fields = ['is_active', 'is_verified', 'country', 'state', 'city']


class SubsidiaryFilter(django_filters.FilterSet):
    """Filter for Subsidiary"""
    organization = django_filters.NumberFilter(field_name='parent_organization__id')
    organization_code = django_filters.CharFilter(field_name='parent_organization__code')
    country = django_filters.NumberFilter(field_name='country__id')
    state = django_filters.NumberFilter(field_name='state__id')
    city = django_filters.NumberFilter(field_name='city__id')
    
    class Meta:
        model = Subsidiary
        fields = ['is_active', 'organization', 'organization_code', 'country', 'state', 'city']


class DepartmentFilter(django_filters.FilterSet):
    """Filter for Department"""
    subsidiary = django_filters.NumberFilter(field_name='subsidiary__id')
    subsidiary_code = django_filters.CharFilter(field_name='subsidiary__code')
    organization = django_filters.NumberFilter(field_name='subsidiary__parent_organization__id')
    organization_code = django_filters.CharFilter(field_name='subsidiary__parent_organization__code')
    department_type = django_filters.ChoiceFilter(choices=Department._meta.get_field('department_type').choices)
    employee_count_min = django_filters.NumberFilter(field_name='employee_count', lookup_expr='gte')
    employee_count_max = django_filters.NumberFilter(field_name='employee_count', lookup_expr='lte')
    
    class Meta:
        model = Department
        fields = ['is_active', 'subsidiary', 'subsidiary_code', 'organization', 
                  'organization_code', 'department_type', 'employee_count_min', 'employee_count_max']