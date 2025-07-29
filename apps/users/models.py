from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    USER_TYPE_CHOICES = (
        ('regular', _('Regular User')),
        ('journalist', _('Journalist')),
        ('editor', _('Editor')),
        ('admin', _('Administrator')),
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='regular',
        verbose_name=_('User Type')
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Is Verified')
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pictures',
        null=True,
        blank=True,
        verbose_name=_('Profile Picture')
    )
    
    cover_photo = models.ImageField(
        upload_to='cover_photos',
        null=True,
        blank=True,
        verbose_name=_('Cover Photo')
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=_('Bio')
    )
    website = models.URLField(
        blank=True,
        verbose_name=_('Website')
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Location')
    )
    twitter = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Twitter')
    )
    facebook = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Facebook')
    )
    instagram = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Instagram')
    )
    linkedin = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('LinkedIn')
    )
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()


class UserInterest(models.Model):
    """
    Model to store user interests/topics they want to follow.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interests')
    name = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('user', 'name')
        verbose_name = _('User Interest')
        verbose_name_plural = _('User Interests')
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class UserFollowing(models.Model):
    """
    Model representing a follow relationship between users
    """
    user = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    following_user = models.ForeignKey(
        User,
        related_name='followers',
        on_delete=models.CASCADE,
        verbose_name=_('Following')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('User Following')
        verbose_name_plural = _('User Followings')
        unique_together = ('user', 'following_user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} follows {self.following_user.username}"
