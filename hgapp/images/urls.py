from django.urls import path

from . import views

app_name = 'image'
urlpatterns = [
    # ex: .com/journals/write/c/291
    path('tiny_upload/', views.upload_image, name='upload_image_tiny'),

    # # ex: .com/journals/write/g/12/c/291
    # path('write/g/<int:game_id>/c/<int:character_id>/', views.WriteGameJournal.as_view(), name='journal_write_game'),
    # # ex: .com/journals/write/c/291
    # path('write/c/<int:character_id>/', views.write_next_journal, name='journal_write_next'),
    # # ex: .com/journals/write/g/12/c/291/downtime
    # path('write/downtime/g/<int:game_id>/c/<int:character_id>/', views.WriteDowntimeJournal.as_view(), name='journal_write_downtime'),
    # # ex: .com/journals/edit/j/21
    # path('edit/j/<int:journal_id>/', views.EditJournal.as_view(), name='journal_edit'),
    # # ex: .com/journals/write/cover/c/291/
    # path('write/cover/c/<int:character_id>/', views.EditCover.as_view(), name='journal_edit_cover'),
    #
    # # ex: .com/journals/read/c/12
    # path('read/c/<int:character_id>/', views.ReadJournal.as_view(), name='journal_read'),
    # # ex: .com/journals/read/c/12/g/21
    # path('read/c/<int:character_id>/g/<int:game_id>/', views.ReadJournal.as_view(), name='journal_read_game'),
    # # ex: .com/journals/read/j/21
    # path('read/j/<int:journal_id>/', views.ReadJournal.as_view(), name='journal_read_id'),
    #
    # # ex: .com/journals/latest
    # path('latest', views.CommunityJournals.as_view(), name='community_journals'),
]
