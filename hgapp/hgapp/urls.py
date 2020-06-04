"""hgapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from django.conf.urls.static import static
from django.views.generic import TemplateView
from hgapp import views

from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^messages/', include('postman.urls', namespace="postman"), name="postman"),
    url(r"^$", views.home, name="home"),
    url(r'^powers/', include('powers.urls'), name="powers"),
    url(r"^account/", include("account.urls")),
    url(r"^profile/", include ("profiles.urls"), name="profile"),
    url(r"^characters/", include ("characters.urls"), name="character"),
    url(r"^games/", include("games.urls"), name="games"),
    url(r"^cells/", include("cells.urls"), name="cells"),
    path('notifications/', include('django_nyt.urls')),
    path('wiki/', include('wiki.urls')),
]

import os
try:
    os.environ['SECRET_KEY']
    DEBUG = False
except:
    DEBUG = True

if DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)