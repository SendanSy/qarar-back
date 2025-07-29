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
    fields = ('name', 'name_ar', 'code', 'is_active')
    readonly_fields = ('created_at',)


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    """Admin configuration for Organization model"""
    
    list_display = [
        'name_display',
        'code',
        'email',
        'phone',
        'country',
        'is_active_display',
        'is_verified_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'is_verified',
        ('country', RelatedDropdownFilter),
        'created_at',
    ]
    
    search_fields = ['name', 'name_ar', 'code', 'email', 'phone', 'website']
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'name_ar'),
                'code',
                ('description', 'description_ar'),
            )
        }),
        (_('Contact Information'), {
            'fields': (
                ('email', 'phone'),
                'website',
            )
        }),
        (_('Location'), {
            'fields': (
                'country',
                'state',
                'city',
            )
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
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SubsidiaryInline]
    autocomplete_fields = ['country', 'state', 'city']
    
    @display(description=_('Name'))
    def name_display(self, obj):
        if obj.name_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.name_ar,
                obj.name or ''
            )
        return obj.name
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    @display(description=_('Verified'), boolean=True)
    def is_verified_display(self, obj):
        return obj.is_verified
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('country', 'state', 'city').prefetch_related('subsidiaries')


@admin.register(Subsidiary)
class SubsidiaryAdmin(ModelAdmin):
    """Admin configuration for Subsidiary model"""
    
    list_display = [
        'name_display',
        'code',
        'parent_organization',
        'country',
        'is_active_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        ('parent_organization', RelatedDropdownFilter),
        ('country', RelatedDropdownFilter),
        'created_at',
    ]
    
    search_fields = [
        'name', 'name_ar',
        'code',
        'parent_organization__name', 'parent_organization__name_ar'
    ]
    
    autocomplete_fields = ['parent_organization', 'country', 'state', 'city']
    ordering = ['parent_organization', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'parent_organization',
                ('name', 'name_ar'),
                'code',
                ('description', 'description_ar'),
            )
        }),
        (_('Location'), {
            'fields': (
                'country',
                'state',
                'city',
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
    
    readonly_fields = ['created_at', 'updated_at']
    
    @display(description=_('Name'))
    def name_display(self, obj):
        if obj.name_ar:
            return format_html(
                '<div style="direction: rtl;">{}</div><small>{}</small>',
                obj.name_ar,
                obj.name or ''
            )
        return obj.name
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent_organization', 'country', 'state', 'city')