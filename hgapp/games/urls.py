from django.conf.urls import url

from . import views


app_name = 'games'
urlpatterns = [
    # ex: .com/games/enter/
    url(r'^enter/$', views.enter_game, name='games_enter_game'),

    # ex: .com/games/create/scenario/
    url(r'^create/scenario/$', views.create_scenario, name='games_create_scenario'),

    # ex: .com/games/edit/s/112
    url(r'^edit/s/(?P<scenario_id>[\d]+)/$', views.edit_scenario, name='games_scenario_edit'),

    # ex: .com/games/view/s/110
    url(r'^view/s/(?P<scenario_id>[\d]+)/$', views.view_scenario, name='games_view_scenario'),

    # ex: .com/games/view/s/110/g/1231
    url(r'^view/s/(?P<scenario_id>[\d]+)/g/(?P<game_id>[\d]+)/$', views.view_scenario, name='games_view_scenario_feedback'),

    # ex: .com/games/view/s/gallery
    url(r'^view/s/gallery/$', views.view_scenario_gallery, name='games_view_scenario_gallery'),

    # ex: .com/games/create/game/
    url(r'^create/game/$', views.create_game, name='games_create_game'),

    # ex: .com/games/edit/g/112
    url(r'^edit/g/(?P<game_id>[\d]+)/$', views.edit_game, name='games_game_edit'),


    # ex: .com/games/create/game/ex/cell/1
    url(r'^create/game/ex/cell/(?P<cell_id>[\d]+)/$',
        views.create_ex_game_for_cell,
        name='games_create_ex_game_for_cell'),

    # ex: .com/games/create/game/ex/cell/1/gm/1241/p/9520+323+412/
    url(r'^create/game/ex/cell/(?P<cell_id>[\d]+)/gm/(?P<gm_user_id>[\d]+)/p/(?P<players>[\d\+]+)/$',
        views.finalize_create_ex_game_for_cell,
        name='games_edit_ex_game_add_players'),

    # ex: .com/games/start/g/112
    # ex: .com/games/start/g/112/char_error=21,1,3
    # ex: .com/games/start/g/112/player_error=12
    # ex: .com/games/start/g/112/player_error=12/char_error=21,1,3
    # url(r'^start/g/(?P<game_id>[\d]+)/$', views.start_game, name='games_start_game'),
    url(r'^start/g/(?P<game_id>[\d]+)(?:/char_error=(?P<char_error>[\d,]+))?(?:/player_error=(?P<player_error>[\d,]+))?/$',
        views.start_game,
        name='games_start_game'),

    # ex: .com/games/confirm_attendance/g/110
    url(r'^confirm_attendance/g/(?P<attendance_id>[\d]+)/$', views.confirm_attendance, name='games_confirm_attendance'),

    # ex: .com/games/confirm_attendance/g/110/y
    url(r'^confirm_attendance/g/(?P<attendance_id>[\d]+)/(?P<confirmed>[yn])/$', views.confirm_attendance, name='games_confirm_attendance'),

    # ex: .com/games/end/g/110
    url(r'^end/g/(?P<game_id>[\d]+)/$', views.end_game, name='games_end_game'),

    # ex: .com/games/view/g/110
    url(r'^view/g/(?P<game_id>[\d]+)/$', views.view_game, name='games_view_game'),

    # ex: .com/games/cancel/g/110
    url(r'^cancel/g/(?P<game_id>[\d]+)/$', views.cancel_game, name='games_cancel_game'),

    # ex: .com/games/invite/g/110
    url(r'^invite/g/(?P<game_id>[\d]+)/$', views.invite_players, name='games_invite_players'),

    # ex: .com/games/accept/g/110
    url(r'^accept/g/(?P<game_id>[\d]+)/$', views.accept_invite, name='games_accept_invite'),

    # ex: .com/games/decline/g/110
    url(r'^decline/g/(?P<game_id>[\d]+)/$', views.decline_invite, name='games_decline_invite'),

    # ex: .com/games/allocate_improvement/i/219
    url(r'^allocate_improvement/i/(?P<improvement_id>[\d]+)/$', views.allocate_improvement, name='games_allocate_improvement'),

    # ex: .com/games/allocate_improvement
    url(r'^allocate_improvement/$', views.allocate_improvement_generic,
        name='games_allocate_improvement_generic'),

    ##################
    # AJAX endpoints
    ##################
    url(r'^post/ajax/spoil-scenario/s/(?P<scenario_id>[\d]+)/$', views.spoil_scenario,
        name="games_spoil_scenario"),
    #
]