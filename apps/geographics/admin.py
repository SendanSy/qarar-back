"""
Admin configuration for geographics app with Django Unfold
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RelatedDropdownFilter
from .models import Country, State, City


class StateInline(TabularInline):
    """Inline for country states"""
    model = State
    extra = 0
    fields = ('name', 'code', 'is_active')
    readonly_fields = ('created_at',)


class CityInline(TabularInline):
    """Inline for state cities"""
    model = City
    extra = 0
    fields = ('name', 'is_active')
    readonly_fields = ('created_at',)


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    """Admin configuration for Country model"""
    
    list_display = [
        'name',
        'code',
        'states_count',
        'is_active_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'created_at',
    ]
    
    search_fields = ['name', 'code']
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'code',
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
    inlines = [StateInline]
    
    @display(description=_('States'))
    def states_count(self, obj):
        count = obj.states.count()
        if count > 0:
            return format_html(
                '<span style="background: #3b82f6; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                count
            )
        return '-'
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('states')


@admin.register(State)
class StateAdmin(ModelAdmin):
    """Admin configuration for State model"""
    
    list_display = [
        'name',
        'code',
        'country_display',
        'cities_count',
        'is_active_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        ('country', RelatedDropdownFilter),
        'created_at',
    ]
    
    search_fields = [
        'name',
        'code',
        'country__name', 'country__code'
    ]
    
    autocomplete_fields = ['country']
    ordering = ['country', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'country',
                'name',
                'code',
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
    inlines = [CityInline]
    
    @display(description=_('Country'), ordering='country')
    def country_display(self, obj):
        if obj.country:
            return obj.country.name
        return '-'
    
    @display(description=_('Cities'))
    def cities_count(self, obj):
        count = obj.cities.count()
        if count > 0:
            return format_html(
                '<span style="background: #3b82f6; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                count
            )
        return '-'
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('country').prefetch_related('cities')


@admin.register(City)
class CityAdmin(ModelAdmin):
    """Admin configuration for City model"""
    
    list_display = [
        'name',
        'state_display',
        'country_display',
        'is_active_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        ('state', RelatedDropdownFilter),
        ('state__country', RelatedDropdownFilter),
        'created_at',
    ]
    
    search_fields = [
        'name',
        'state__name',
        'state__country__name'
    ]
    
    autocomplete_fields = ['state']
    ordering = ['state__country', 'state', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'state',
                'name',
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
    
    @display(description=_('State'), ordering='state')
    def state_display(self, obj):
        if obj.state:
            return obj.state.name
        return '-'
    
    @display(description=_('Country'))
    def country_display(self, obj):
        if obj.state and obj.state.country:
            return obj.state.country.name
        return '-'
    
    @display(description=_('Active'), boolean=True)
    def is_active_display(self, obj):
        return obj.is_active
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('state', 'state__country')