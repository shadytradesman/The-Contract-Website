from django.conf.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r"^", include("blog.urls", namespace="pinax_blog")),
]
