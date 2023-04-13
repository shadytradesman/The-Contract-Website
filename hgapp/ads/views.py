from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from .models import FakeAd
from .forms import AdForm
from django.db import transaction


def edit_ad(request, ad_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise PermissionDenied("You cannot edit the ads")
    ad = get_object_or_404(FakeAd, id=ad_id)
    if request.method == 'POST':
        form = AdForm(request.POST, instance=ad)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            return HttpResponseRedirect("/")
        else:
            raise ValueError("invalid form")
    else:
        form = AdForm(instance=ad)
        context = {
            'form': form,
            'ad': ad,
        }
        return render(request, 'ads/edit_ad.html', context)

