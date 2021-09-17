from django.urls import path


from . import views

app_name = 'guide'
urlpatterns = [
    # ex: .com/guide/rules/
    # ex: .com/guide/rules/#attributes
    path('<slug:guidebook_slug>/', views.ReadGuideBook.as_view(), name='read_guidebook'),
]
