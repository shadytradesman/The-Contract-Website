from django.urls import path


from . import views

app_name = 'journals'
urlpatterns = [
    # ex: .com/journals/write/g/12/c/291
    path('write/g/<int:game_id>/c/<int:character_id>/', views.WriteJournal.as_view(), name='journal_write'),
]