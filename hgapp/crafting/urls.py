from django.urls import path

from . import views


app_name = 'crafting'
urlpatterns = [
    # ex: .com/crafting/c/21
    path('c/<int:character_id>/', views.Craft.as_view(), name='crafting_craft'),
]