from django.conf.urls import url
from . import views

app_name = 'info'
urlpatterns = [

    # ex: .com/info/terms/
    url(r"^terms/$", views.terms, name="terms"),

    # ex: .com/info/probability/
    url(r"^probability/$", views.probability, name="probability"),

    # ex: .com/info/leaderboard/
    url(r"^leaderboard/$", views.leaderboard, name="leaderboard"),

    # ex: .com/info/fiction/
    url(r"^fiction/$", views.fiction, name="fiction"),

    # ex: .com/info/quickstart/
    url(r"^how-to-play/$", views.how_to_play, name="how-to-play"),
]
