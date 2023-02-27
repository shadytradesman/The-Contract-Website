from django.shortcuts import render
from django.db import transaction
from .models import PlayerLastReadTime, Notification

def nav_read(request):
    if not request.user.is_authenticated:
        return render(request, 'notifications/nav_list.html', {"auth_error":True})
    with transaction.atomic():
        new_notifs = Notification.get_unread_notifications_for_player_queryset(request.user)
        num_unread = Notification.get_num_unread_notifications_for_player(request.user)
        num_read_to_fetch = max(25 - num_unread, 0)
        read_notifs = Notification.objects.none()
        if num_read_to_fetch > 0:
            read_notifs = Notification.get_read_notifications_for_player_queryset(request.user, num_read_to_fetch)
        context = {
            "num_unread": num_unread,
            "new_notifs": new_notifs,
            "read_notifs": read_notifs
        }
        PlayerLastReadTime.update_last_read_for_player(request.user)
    return render(request, 'notifications/nav_list.html', context)




