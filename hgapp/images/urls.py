from django.urls import path

from . import views

app_name = 'image'
urlpatterns = [
    # ex: .com/image/tiny_upload/
    path('tiny_upload/', views.upload_image_tiny, name='upload_image_tiny'),

    path('upload/<', views.upload_image, name='upload_image'),
]
