from django.urls import re_path
from django.views.generic.base import RedirectView
from . import views

app_name = 'info'
urlpatterns = [

    # ex: .com/info/terms/
    re_path(r"^terms/$", views.terms, name="terms"),

    # ex: .com/info/discord-bot/
    re_path(r"^discord-bot/$", views.bot, name="bot"),

    # ex: .com/info/probability/
    re_path(r"^probability/$", views.probability, name="probability"),

    # ex: .com/info/hall-of-fame
    re_path(r"^hall-of-fame/$", views.leaderboard, name="leaderboard"),

    # ex: .com/info/community-records/
    re_path(r"^community-records/$", RedirectView.as_view(pattern_name='info:leaderboard', permanent=True)),

    # ex: .com/info/statistics/
    re_path(r"^statistics/$",
        RedirectView.as_view(pattern_name='info:leaderboard', permanent=True)),

    # ex: .com/info/vibes/
    re_path(r"^vibes/$", views.vibes, name="vibes"),

    # ex: .com/info/how-to-play/
    re_path(r"^how-to-play/$", views.how_to_play, name="how-to-play"),

    # ex: .com/info/learn-to-play/
    re_path(r"^learn-to-play/$", views.learn_to_play, name="learn-to-play"),

    # ex: .com/info/printable-quickstart
    re_path(r"^printable-quickstart/$", views.printable_quickstart, name="printable_quickstart"),
]
