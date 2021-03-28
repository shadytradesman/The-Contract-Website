from django.urls import path


from . import views

app_name = 'journals'
urlpatterns = [
    # ex: .com/journals/write/g/12/c/291
    path('write/g/<int:game_id>/c/<int:character_id>/', views.WriteGameJournal.as_view(), name='journal_write_game'),
    # ex: .com/journals/write/g/12/c/291/downtime
    path('write/downtime/g/<int:game_id>/c/<int:character_id>/', views.WriteDowntimeJournal.as_view(), name='journal_write_downtime'),

    # ex: .com/journals/read/c/12
    path('read/c/<int:character_id>/', views.ReadJournal.as_view(), name='journal_read'),
    # ex: .com/journals/read/c/12/g/21
    path('read/c/<int:character_id>/g/<int:game_id>/', views.ReadJournal.as_view(), name='journal_read'),
]