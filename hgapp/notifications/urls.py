from django.urls import re_path
from .views import nav_read

app_name = 'notifications'
urlpatterns = [
    # ex: .com/notification/nav-read
    re_path(r'^nav-read/$', nav_read, name='notifications_nav_read'),
]
