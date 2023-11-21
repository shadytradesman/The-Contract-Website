from .tasks import generate_thumbnail
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from .models import PrivateUserImage


@receiver(post_save, sender=PrivateUserImage, dispatch_uid="generate_thumbnail_receiver")
def generate_thumbnail_receiver(sender, instance, created, **kwargs):
    if created:
        return generate_thumbnail.delay(instance.pk)
