from rest_framework import serializers
from .models import Organization, Subsidiary, Department


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for Organization
    """
    subsidiary_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'name_ar', 'code', 'description', 'description_ar',
            'website', 'email', 'phone', 'country', 'state', 'city',
            'is_active', 'is_verified', 'subsidiary_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'subsidiary_count')
    
    def get_subsidiary_count(self, obj):
        return obj.subsidiaries.filter(is_active=True).count()


class SubsidiarySerializer(serializers.ModelSerializer):
    """
    Serializer for Subsidiary
    """
    parent_organization_name = serializers.CharField(source='parent_organization.name', read_only=True)
    parent_organization_name_ar = serializers.CharField(source='parent_organization.name_ar', read_only=True)
    department_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subsidiary
        fields = (
            'id', 'name', 'name_ar', 'code', 'parent_organization',
            'parent_organization_name', 'parent_organization_name_ar',
            'description', 'description_ar', 'country', 'state', 'city',
            'is_active', 'department_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'department_count')
    
    def get_department_count(self, obj):
        return obj.departments.filter(is_active=True).count()


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Department
    """
    subsidiary_name = serializers.CharField(source='subsidiary.name', read_only=True)
    subsidiary_name_ar = serializers.CharField(source='subsidiary.name_ar', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_name_ar = serializers.CharField(source='organization.name_ar', read_only=True)
    department_type_display = serializers.CharField(source='get_department_type_display', read_only=True)
    
    class Meta:
        model = Department
        fields = (
            'id', 'name', 'name_ar', 'code', 'subsidiary', 'subsidiary_name',
            'subsidiary_name_ar', 'organization_name', 'organization_name_ar',
            'description', 'description_ar', 'head_name', 'head_email', 'head_phone',
            'employee_count', 'department_type', 'department_type_display',
            'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'department_type_display')


class DepartmentMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for Department (for use in dropdowns/lists)
    """
    class Meta:
        model = Department
        fields = ('id', 'name', 'name_ar', 'code')