from django.conf import settings
from django.urls import include
from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from hgapp import views
from django_ses.views import SESEventWebhookView

from django.contrib import admin

urlpatterns = [
    re_path(r'^kickstart/', RedirectView.as_view(url='https://www.kickstarter.com/projects/sapientsnake/the-contract-rpg?ref=3tpmim'), name="kickstart"),
    re_path(r'^kickstarter/', RedirectView.as_view(url='https://www.kickstarter.com/projects/sapientsnake/the-contract-rpg?ref=3tpmim'), name="kickstarter"),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^messages/', include('postman.urls', namespace="postman"), name="postman"),
    re_path(r"^$", views.home, name="home"),
    re_path(r"^home/contractors$", views.logged_in_contractors, name="logged_in_contractors"),
    re_path(r'^gift/', include('powers.urls'), name="powers"),
    re_path(r'^powers/', views.RedirectRootUrlView.as_view(new_root="/gift", permanent="true")),
    re_path(r"^account/signup/$", views.SignupView.as_view(), name="account_signup"),
    re_path(r"^account/login/$", views.LoginView.as_view(), name="account_signup"),
    re_path(r"^account/settings/$", views.SettingsView.as_view(), name="account_settings"),
    re_path(r"^account/resend-confirmation/$", views.ResendConfirmation.as_view(), name="account_resend_confirmation"),
    re_path(r"^account/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$", views.PasswordResetTokenView.as_view(),
        name="account_password_reset_token"),
    re_path(r"^account/", include("account.urls")),
    re_path(r'^ses/event-webhook/$', SESEventWebhookView.as_view(), name='handle_event_webhook'),
    re_path(r"^profile/", include("profiles.urls"), name="profile"),
    re_path(r"^contractor/", include("characters.urls"), name="character"),
    re_path(r'^characters/', views.RedirectRootUrlView.as_view(new_root="/contractor", permanent="true")),
    re_path(r"^contract/", include("games.urls"), name="games"),
    re_path(r'^games/', views.RedirectRootUrlView.as_view(new_root="/contract", permanent="true")),
    re_path(r"^playgroup/", include("cells.urls"), name="cells"),
    re_path(r'^groups/', views.RedirectRootUrlView.as_view(new_root="/playgroup", permanent="true")),
    re_path(r"^info/", include("info.urls"), name="info"),
    re_path(r"^guide/", include("guide.urls"), name="guide"),
    re_path(r"^image/", include("images.urls"), name="image"),
    re_path(r"^report/", include("reporting.urls"), name="reporting"),
    re_path(r"^journal/", include("journals.urls"), name="journals"),
    re_path(r"^journals/*", views.RedirectRootUrlView.as_view(new_root="/journal", permanent="true")),
    re_path(r"^crafting/", include("crafting.urls"), name="crafting"),
    re_path(r"^notification/", include("notifications.urls"), name="notifications"),
    re_path(r"^ad/", include("ads.urls"), name="ads"),
    re_path(r"^questionnaire/", include("questionnaire.urls"), name="questionnaire"),
    re_path(r"^tinymce/", include("tinymce.urls")),
    re_path(r"^news/", include("blog.urls", namespace="pinax_blog")),
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