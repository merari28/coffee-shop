from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """Extra public-facing info for each user (avatar shown across the UI)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="usuario",
    )
    avatar = models.ImageField(
        upload_to="avatars",
        null=True,
        blank=True,
        verbose_name="foto de perfil",
    )
    bio = models.CharField(max_length=200, blank=True, verbose_name="biografía")

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    """Every user automatically gets a Profile row."""
    if created:
        Profile.objects.get_or_create(user=instance)
