from django.contrib import admin
from .models import Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country', 'is_active', 'is_verified')
    list_filter = ('is_active', 'is_verified', 'country')
    search_fields = ('name', 'name_ar', 'code')
    ordering = ('name',) 