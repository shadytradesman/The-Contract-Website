from django.conf.urls import url
from .views import nav_read

app_name = 'notifications'
urlpatterns = [
    # ex: .com/notification/nav-read
    url(r'^nav-read/$', nav_read, name='notifications_nav_read'),
]
