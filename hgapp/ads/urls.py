from django.urls import path


from . import views

app_name = 'ads'
urlpatterns = [
    # ex: .com/ad/edit/2
    path('edit/<int:ad_id>/', views.edit_ad, name='edit_ad'),
]
