from django.http import HttpResponseRedirect, HttpResponse,JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from .models import UserImage
from games.models import Scenario


@login_required
def upload_image_tiny(request):
    if request.user.is_anonymous or not request.user.is_authenticated:
        return JsonResponse({"error": "Must be logged in"}, status=403)
    if request.POST:
        scenario_id = request.POST["scenario"]
        if scenario_id:
            scenario = get_object_or_404(Scenario, pk=scenario_id)
            if not scenario.player_can_edit_writeup(request.user):
                return JsonResponse({"error": "Cannot edit Scenario"}, status=403)
        else:
            scenario = None
        new_image = UserImage(
            uploader=request.user,
            image=request.FILES["file"],
            scenario=scenario)
        with transaction.atomic():
            new_image.save()
        return JsonResponse({"location": new_image.image.url}, status=200)
    return JsonResponse({"error": "invalid request type"}, status=500)


@login_required
def upload_image(request):
    if not request.user.is_authenticated and request.user.profile.early_access_user:
        raise PermissionError("Early Access only")

    if request.POST:
        scenario_id = request.POST["scenario"]
        if scenario_id:
            scenario = get_object_or_404(Scenario, pk=scenario_id)
            if not scenario.player_can_edit_writeup(request.user):
                return JsonResponse({"error": "Cannot edit Scenario"}, status=403)
        else:
            scenario = None
        new_image = UserImage(
            uploader=request.user,
            image=request.FILES["file"],
            scenario=scenario)
        with transaction.atomic():
            new_image.save()
        return JsonResponse({"location": new_image.image.url}, status=200)
    return JsonResponse({"error": "invalid request type"}, status=500)
