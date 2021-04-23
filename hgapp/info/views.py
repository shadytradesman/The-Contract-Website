from django.shortcuts import render
from .terms import EULA, TERMS, PRIVACY
from info.models import FrontPageInfo

def getting_started(request):
    return render(request, 'info/getting_started.html')

def terms(request):
    context= {
        "terms": TERMS,
        "eula": EULA,
        "privacy": PRIVACY,
    }
    return render(request, 'info/terms.html', context)

def probability(request):
    return render(request, 'info/probability.html')

def fiction(request):
    info = FrontPageInfo.objects.first()
    context= {
        "info": info,
    }
    return render(request, 'info/fiction.html', context)
