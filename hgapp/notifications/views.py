from django.shortcuts import render
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from .models import PlayerLastReadTime, Notification
from itertools import chain

def set_read(request):
    if not request.user.is_authenticated:
        return JsonResponse({}, status=403)
    else:
        if request.is_ajax and request.method == "POST":
            with transaction.atomic():
                PlayerLastReadTime.update_last_read_for_player(request.user)
            return JsonResponse({}, status=200)
        return JsonResponse({"error": ""}, status=400)

def nav_read(request):
    if not request.user.is_authenticated:
        return render(request, 'notifications/nav_list.html', {"auth_error":True})
    with transaction.atomic():
        new_notifs = Notification.get_unread_notifications_for_player_queryset(request.user)
        notificaitons = new_notifs
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




