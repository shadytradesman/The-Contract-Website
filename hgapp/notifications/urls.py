from django.conf.urls import url
from .views import set_read, nav_read

app_name = 'notifications'
urlpatterns = [
    # ex: .com/notification/set-read/
    url(r'^set-read/$', set_read, name='notifications_set_read'),

    # ex: .com/notification/nav-read
    url(r'^nav-read/$', nav_read, name='notifications_nav_read'),
]
