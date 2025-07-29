"""
Admin configuration for producers app with Django Unfold
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RelatedDropdownFilter
from .models import Organization, Subsidiary


class SubsidiaryInline(TabularInline):
    """Inline for organization subsidiaries"""
    model = Subsidiary
    extra = 0
    fields = ('name', 'name_ar', 'email', 'phone', 'is_active')
    readonly_fields = ('created_at',)


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    """Admin configuration for Organization model"""
    
    list_display = [
        'name_display',
        'code',
        'organization_type_display',
        'email',
        'phone',
        'subsidiaries_count',
        'is_active_display',
        'is_verified_display',
        'created_at',
    ]
    
    list_filter = [
        'organization_type',
        'is_active',
        'is_verified',
        'country',
        'created_at',
    ]
    
    search_fields = ['name', 'name_ar', 'code', 'email', 'phone', 'website']
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'name_ar'),
                'slug',
                ('code', 'organization_type'),
                ('description', 'description_ar'),
            )
        }),
        (_('Contact Information'), {
            'fields': (
                ('email', 'phone'),
                'website',
                'address',
                'country',
            )
        }),
        (_('Media'), {
            'fields': (
                'logo',
                'cover_image',
            ),
            'classes': ('collapse',),
        }),
        (_('Status'), {
            'fields': (
                'is_active',
                'is_verified',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['slug', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SubsidiaryInline]
    
    @display(description=_('Name'))
    def name_display(self, obj):
        if obj.name_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.name_ar,
                obj.name or ''
            )
        return obj.name
    
    @display(description=_('Type'), ordering='organization_type')
    def organization_type_display(self, obj):
        types = {
            'government': {'label': _('Government'), 'color': '#dc2626'},
            'ministry': {'label': _('Ministry'), 'color': '#2563eb'},
            'department': {'label': _('Department'), 'color': '#7c3aed'},
            'agency': {'label': _('Agency'), 'color': '#16a34a'},
            'other': {'label': _('Other'), 'color': '#6b7280'},
        }
        type_info = types.get(obj.organization_type, {'label': obj.organization_type, 'color': '#6b7280'})
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            type_info['color'],
            type_info['label']
        )
    
    @display(description=_('Subsidiaries'))
    def subsidiaries_count(self, obj):
        count = obj.subsidiaries.filter(is_deleted=False).count()
        if count > 0:
            return format_html(
                '<span style="background: #3b82f6; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                count
            )
        return '-'
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    @display(description=_('Verified'), boolean=True)
    def is_verified_display(self, obj):
        return obj.is_verified
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('subsidiaries')


@admin.register(Subsidiary)
class SubsidiaryAdmin(ModelAdmin):
    """Admin configuration for Subsidiary model"""
    
    list_display = [
        'name_display',
        'organization_display',
        'email',
        'phone',
        'is_active_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        ('organization', RelatedDropdownFilter),
        'created_at',
    ]
    
    search_fields = [
        'name', 'name_ar',
        'email', 'phone',
        'organization__name', 'organization__name_ar'
    ]
    
    autocomplete_fields = ['organization']
    ordering = ['organization', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'organization',
                ('name', 'name_ar'),
                'slug',
                ('description', 'description_ar'),
            )
        }),
        (_('Contact Information'), {
            'fields': (
                ('email', 'phone'),
                'address',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['slug', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    
    @display(description=_('Name'))
    def name_display(self, obj):
        if obj.name_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.name_ar,
                obj.name or ''
            )
        return obj.name
    
    @display(description=_('Organization'), ordering='organization')
    def organization_display(self, obj):
        if obj.organization:
            return obj.organization.name_ar or obj.organization.name
        return '-'
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('organization')