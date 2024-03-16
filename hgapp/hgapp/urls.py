from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from django.views.generic.base import RedirectView
from django.shortcuts import redirect
from django.conf.urls.static import static
from hgapp import views
from django_ses.views import SESEventWebhookView
from django.views.decorators.csrf import csrf_exempt

from django.contrib import admin

urlpatterns = [
    url(r'^kickstart/', RedirectView.as_view(url='https://www.kickstarter.com/projects/sapientsnake/the-contract-rpg?ref=3tpmim'), name="kickstart"),
    url(r'^kickstarter/', RedirectView.as_view(url='https://www.kickstarter.com/projects/sapientsnake/the-contract-rpg?ref=3tpmim'), name="kickstarter"),
    url(r'^admin/', admin.site.urls),
    url(r'^messages/', include('postman.urls', namespace="postman"), name="postman"),
    url(r"^$", views.home, name="home"),
    url(r"^home/contractors$", views.logged_in_contractors, name="logged_in_contractors"),
    url(r'^gift/', include('powers.urls'), name="powers"),
    url(r'^powers/', views.RedirectRootUrlView.as_view(new_root="/gift", permanent="true")),
    url(r"^account/signup/$", views.SignupView.as_view(), name="account_signup"),
    url(r"^account/login/$", views.LoginView.as_view(), name="account_signup"),
    url(r"^account/settings/$", views.SettingsView.as_view(), name="account_settings"),
    url(r"^account/resend-confirmation/$", views.ResendConfirmation.as_view(), name="account_resend_confirmation"),
    url(r"^account/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$", views.PasswordResetTokenView.as_view(),
        name="account_password_reset_token"),
    url(r"^account/", include("account.urls")),
    url(r'^ses/event-webhook/$', SESEventWebhookView.as_view(), name='handle_event_webhook'),
    url(r"^profile/", include("profiles.urls"), name="profile"),
    url(r"^contractor/", include("characters.urls"), name="character"),
    url(r'^characters/', views.RedirectRootUrlView.as_view(new_root="/contractor", permanent="true")),
    url(r"^contract/", include("games.urls"), name="games"),
    url(r'^games/', views.RedirectRootUrlView.as_view(new_root="/contract", permanent="true")),
    url(r"^playgroup/", include("cells.urls"), name="cells"),
    url(r'^groups/', views.RedirectRootUrlView.as_view(new_root="/playgroup", permanent="true")),
    url(r"^info/", include("info.urls"), name="info"),
    url(r"^guide/", include("guide.urls"), name="guide"),
    url(r"^image/", include("images.urls"), name="image"),
    url(r"^report/", include("reporting.urls"), name="reporting"),
    url(r"^journal/", include("journals.urls"), name="journals"),
    url(r"^journals/*", views.RedirectRootUrlView.as_view(new_root="/journal", permanent="true")),
    url(r"^crafting/", include("crafting.urls"), name="crafting"),
    url(r"^notification/", include("notifications.urls"), name="notifications"),
    url(r"^ad/", include("ads.urls"), name="ads"),
    url(r"^questionnaire/", include("questionnaire.urls"), name="questionnaire"),
    url(r"^tinymce/", include("tinymce.urls")),
    url(r"^news/", include("blog.urls", namespace="pinax_blog")),
    url(r"^ajax/images/", include("pinax.images.urls", namespace="pinax_images")),
]

import os
try:
    os.environ['SECRET_KEY']
    DEBUG = False
except:
    DEBUG = True

if DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))