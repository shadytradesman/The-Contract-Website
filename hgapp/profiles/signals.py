from account.signals import user_signed_up
from django.dispatch import receiver
from guardian.shortcuts import assign_perm
from profiles.models import Profile
from django.utils import timezone

@receiver(user_signed_up)
def make_profile_for_new_user(sender, user, **kwargs):
    new_profile = Profile(user = user,
                          id = user.id,
                          confirmed_agreements=True,
                          date_confirmed_agreements = timezone.now)
    new_profile.save()
    assign_perm('change_profile', user, new_profile)
