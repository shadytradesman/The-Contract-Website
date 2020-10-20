from django.conf.urls import url
from . import views


app_name = 'info'
urlpatterns = [
    # ex: .com/info/getting-started/
    url(r"^getting-started/$", views.getting_started, name="getting_started"),

    # ex: .com/info/terms/
    url(r"^terms/$", views.terms, name="terms"),

    # ex: .com/info/probability/
    url(r"^probability/$", views.probability, name="probability"),

]
