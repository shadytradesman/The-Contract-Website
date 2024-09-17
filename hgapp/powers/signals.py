from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from guardian.shortcuts import assign_perm
from django.contrib.auth.models import User

from powers.models import Power, Power_Full, Base_Power

@receiver(post_save, sender=Power, dispatch_uid="create_power")
def set_new_power_perms(sender, instance, created, **kwargs):
    if instance.created_by:
        assign_perm('view_power', instance.created_by, instance)
        assign_perm('view_private_power', instance.created_by, instance)
        for user in User.objects.filter(is_superuser=True).all():
            assign_perm('view_private_power', user, instance)

@receiver(post_save, sender=Power_Full, dispatch_uid="create_power_full")
def set_new_power_full_perms(sender, instance, created, **kwargs):
    #change to if created and instance.owner
    #this is kept this way so that I can manually upgrade all extant powers with new permissions.
    if instance.owner:
        assign_perm('view_power_full', instance.owner, instance)
        assign_perm('view_private_power_full', instance.owner, instance)
        assign_perm('edit_power_full', instance.owner, instance)
        for user in User.objects.filter(is_superuser=True).all():
            assign_perm('view_private_power_full', user, instance)


gift_revision = Signal(providing_args=['old_power', 'new_power', 'power_full'])
gift_major_revision = Signal(providing_args=['old_power', 'new_power', 'power_full'])
gift_adjustment = Signal(providing_args=['old_power', 'new_power', 'power_full'])
