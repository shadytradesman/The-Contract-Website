from celery import shared_task

from .models import Notification
from profiles.models import Profile


@shared_task(name="prune_notifications")
def prune_notifications():
    total = 0
    for profile in Profile.objects.all():
        notifs_pks = (Notification.objects.filter(user=profile.user).order_by('-created_date').values_list('pk')[200:])
        total += len(notifs_pks)
        if len(notifs_pks) > 0:
            print("{} deleting {} notifs".format(profile.user.username, len(notifs_pks)))
            Notification.objects.filter(pk__in=notifs_pks).delete()
    print("Deleted {} notifs".format(total))
    return "Completed successfully"

