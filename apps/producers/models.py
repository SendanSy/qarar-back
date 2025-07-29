from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.geographics.models import Country, State, City


class Organization(models.Model):
    """
    Main model for organizations that produce content
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    name_ar = models.CharField(
        max_length=255,
        verbose_name=_('Arabic Name')
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Organization Code')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Description')
    )
    website = models.URLField(
        blank=True,
        verbose_name=_('Website')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email')
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Phone')
    )
    
    # Location information
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name=_('Country')
    )
    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name=_('State')
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name=_('City')
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Verified Status')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Subsidiary(models.Model):
    """
    Model for subsidiary organizations that belong to a parent organization
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    name_ar = models.CharField(
        max_length=255,
        verbose_name=_('Arabic Name')
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Subsidiary Code')
    )
    parent_organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='subsidiaries',
        verbose_name=_('Parent Organization')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Description')
    )
    
    # Location information (can be different from parent)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subsidiaries',
        verbose_name=_('Country')
    )
    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subsidiaries',
        verbose_name=_('State')
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subsidiaries',
        verbose_name=_('City')
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Subsidiary')
        verbose_name_plural = _('Subsidiaries')
        ordering = ['parent_organization', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.parent_organization.name})"


class Department(models.Model):
    """
    Model for departments within subsidiaries
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    name_ar = models.CharField(
        max_length=255,
        verbose_name=_('Arabic Name')
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Department Code')
    )
    subsidiary = models.ForeignKey(
        Subsidiary,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_('Subsidiary')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name=_('Arabic Description')
    )
    
    # Department head information
    head_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Department Head Name')
    )
    head_email = models.EmailField(
        blank=True,
        verbose_name=_('Department Head Email')
    )
    head_phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Department Head Phone')
    )
    
    # Additional department info
    employee_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Number of Employees')
    )
    department_type = models.CharField(
        max_length=50,
        choices=[
            ('admin', _('Administrative')),
            ('media', _('Media')),
            ('technical', _('Technical')),
            ('financial', _('Financial')),
            ('legal', _('Legal')),
            ('hr', _('Human Resources')),
            ('it', _('Information Technology')),
            ('other', _('Other'))
        ],
        default='other',
        verbose_name=_('Department Type')
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        ordering = ['subsidiary', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['department_type']),
        ]
        unique_together = [['subsidiary', 'code']]

    def __str__(self):
        return f"{self.name} - {self.subsidiary.name}"
    
    @property
    def organization(self):
        """Get the parent organization through subsidiary"""
        return self.subsidiary.parent_organization 