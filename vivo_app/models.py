from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    """
    Extended user profile information.
    This model has a one-to-one relationship with the built-in User model.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('user'))

    # Personal Information
    title = models.CharField(
        max_length=100, blank=True, verbose_name=_('title'), help_text=_('Professional title or position')
    )

    institution = models.CharField(
        max_length=255, blank=True, verbose_name=_('institution'), help_text=_('Affiliated institution')
    )

    department = models.CharField(
        max_length=255, blank=True, verbose_name=_('department'), help_text=_('Department or unit')
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name=_('phone number'), help_text=_('Contact phone number'))

    orcid_id = models.CharField(
        max_length=19, blank=True, verbose_name=_('ORCID iD'), help_text=_('ORCID iD (e.g., 0000-0002-1825-0097)')
    )

    # Profile settings
    email_confirmed = models.BooleanField(default=False, verbose_name=_('email confirmed'))

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('last updated'))

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s profile"


# Signal to create/update the user profile when User instances are saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update the user profile when a User object is saved."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # For existing users, just save the profile
        instance.profile.save()
