from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse,JsonResponse
from django.db import transaction

from.models import UserImage


def upload_image(request):
    if request.user.is_anonymous or not request.user.is_authenticated:
        return JsonResponse({"error": "Must be logged in"}, status=403)
    if request.POST:
        new_image = UserImage(
            uploader=request.user,
            image=request.FILES["file"])
        with transaction.atomic():
            new_image.save()
        return JsonResponse({"location": new_image.image.url}, status=200)
    return JsonResponse({"error": "invalid request type"}, status=500)
