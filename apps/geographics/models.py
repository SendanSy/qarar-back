from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    """Base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Country(TimestampedModel):
    """
    Level 1 geographic entity representing countries
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Name')
    )
    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name=_('Country Code'),
        help_text=_('ISO 3166-1 alpha-3 country code')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.name


class State(TimestampedModel):
    """
    Level 2 geographic entity representing states/provinces
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_('State Code')
    )
    country = models.ForeignKey(
        'Country',
        on_delete=models.CASCADE,
        related_name='states',
        verbose_name=_('Country')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )

    class Meta:
        verbose_name = _('State')
        verbose_name_plural = _('States')
        ordering = ['country', 'name']
        unique_together = ['country', 'code']
        indexes = [
            models.Index(fields=['country', 'code']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class City(TimestampedModel):
    """
    Level 3 geographic entity representing cities
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_('City Code')
    )
    state = models.ForeignKey(
        'State',
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name=_('State')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active Status')
    )

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ['state', 'name']
        unique_together = ['state', 'code']
        indexes = [
            models.Index(fields=['state', 'code']),
        ]

    def __str__(self):
        return f"{self.name}, {self.state.name}" 