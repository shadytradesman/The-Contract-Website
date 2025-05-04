from django.urls import path, re_path

from . import views
from django.views.generic.base import RedirectView


app_name = 'games'
urlpatterns = [
    # ex: .com/contract/enter/
    re_path(r'^enter/$', views.enter_game, name='games_enter_game'),

    # ex: .com/contract/other-scenarios/1
    path('other-scenarios/<int:game_id>/', views.view_other_scenarios, name='other_scenarios'),

    # ex: .com/contract/activity/
    re_path(r'^activity/$', views.activity, name='games_activity'),

    # ex: .com/contract/activity/
    re_path(r'^contract-data/$', views.contract_data, name='games_data'),

    # ex: .com/contract/create/scenario/
    re_path(r'^scenario/create$', views.create_scenario, name='games_create_scenario'),
    re_path(r'^create/scenario/$',
        RedirectView.as_view(pattern_name='games:games_create_scenario', query_string=True, permanent=True)),

    # ex: .com/contract/scenario/edit/112
    re_path(r'^scenario/edit/(?P<scenario_id>[\d]+)/$', views.edit_scenario, name='games_scenario_edit'),
    re_path(r'^edit/s/(?P<scenario_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='games:games_scenario_edit', query_string=True, permanent=True)),

    # ex: .com/contract/scenario/submit/112
    re_path(r'^scenario/submit/(?P<scenario_id>[\d]+)/$', views.submit_scenario, name='games_scenario_submit'),

    # ex: .com/contract/scenario/share/112
    re_path(r'^scenario/share/(?P<scenario_id>[\d]+)/$', views.share_scenario, name='games_scenario_share'),

    # ex: .com/contract/scenario/retract/112
    re_path(r'^scenario/retract/(?P<scenario_id>[\d]+)/$', views.retract_scenario, name='games_scenario_retract'),

    # ex: .com/contract/scenario/approvals/
    re_path(r'^scenario/approvals/$', views.approve_scenarios, name='games_scenario_approve'),

    # ex: .com/contract/scenario/approve/112
    re_path(r'^scenario/approve/(?P<scenario_id>[\d]+)/$', views.approve_scenario, name='games_scenario_approve_specific'),

    # ex: .com/contract/scenario/exchange/
    re_path(r'^scenario/exchange/$', views.scenario_exchange, name='games_scenario_exchange'),

    # ex: .com/contract/scenario/exchange/unlock/122
    re_path(r'^scenario/exchange/unlock/(?P<scenario_id>[\d]+)/$', views.purchase_scenario, name='games_scenario_purchase'),

    # ex: .com/contract/scenario/unlock/122
    re_path(r'^scenario/unlock/(?P<scenario_id>[\d]+)/$', views.unlock_scenario, name='games_scenario_unlock'),

    # ex: .com/contract/scenario/110
    re_path(r'^scenario/(?P<scenario_id>[\d]+)/$', views.view_scenario, name='games_view_scenario'),
    re_path(r'^view/s/(?P<scenario_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='games:games_view_scenario', query_string=True, permanent=True)),

    re_path(r'^scenario/(?P<scenario_id>[\d]+)/spoil$', views.spoil_scenario, name='games_spoil_scenario'),

    path('scenario/history/<int:scenario_id>/', views.view_scenario_history, name='scenario_history'),

    path('scenario/spoil-aftermath/<int:scenario_id>/<str:reason>/', views.spoil_aftermath, name='spoil_scenario_aftermath'),

    # ex: .com/contract/view/s/110/g/1231
    re_path(r'^view/s/(?P<scenario_id>[\d]+)/g/(?P<game_id>[\d]+)/$', views.view_scenario, name='games_view_scenario_feedback'),

    # ex: .com/contract/scenario/gallery
    re_path(r'^scenario/gallery/$', views.view_scenario_gallery, name='games_view_scenario_gallery'),
    re_path(r'^view/s/gallery/$',
        RedirectView.as_view(pattern_name='games:games_view_scenario_gallery', query_string=True, permanent=True)),

    # ex: .com/contract/create/
    re_path(r'^create/$', views.create_game, name='games_create_game'),
    # ex: .com/contract/create/p/121
    re_path(r'^create/p/(?P<cell_id>[\d]+)/$', views.create_game, name='games_create_game_world'),

    # ex: .com/contract/edit/112
    re_path(r'^edit/(?P<game_id>[\d]+)/$', views.edit_game, name='games_game_edit'),

    # ex: .com/contract/add-attendance/g/112/
    re_path(r'^add-attendance/g/(?P<game_id>[\d]+)/$',
        views.add_attendance,
        name='games_add_attendance'),

    # ex: .com/contract/edit-completed/112/u/9520+323+412/
    # ex: .com/contract/edit-completed/112/
    re_path(r'^edit-completed/(?P<game_id>[\d]+)/u/(?P<players>[\d\+]*)/$',
        views.edit_completed,
        name='games_edit_completed'),
    re_path(r'^edit-completed/(?P<game_id>[\d]+)/$',
        views.edit_completed,
        name='games_edit_completed'),

    # ex: .com/contract/create-archived/p/1
    re_path(r'^create-archived/p/(?P<cell_id>[\d]+)/$',
        views.create_ex_game_for_cell,
        name='games_create_ex_game_for_cell'),

    # ex: .com/contract/create-archived/p/1/gm/1241/u/9520+323+412/
    re_path(r'^create-archived/p/(?P<cell_id>[\d]+)/gm/(?P<gm_user_id>[\d]+)/u/(?P<players>[\d\+]+)/$',
        views.finalize_create_ex_game_for_cell,
        name='games_edit_ex_game_add_players'),

    # ex: .com/contract/start/112
    # ex: .com/contract/start/112/char_error=21,1,3
    # ex: .com/contract/start/112/player_error=12
    # ex: .com/contract/start/112/player_error=12/char_error=21,1,3
    # re_path(r'^start/g/(?P<game_id>[\d]+)/$', views.start_game, name='games_start_game'),
    re_path(r'^start/(?P<game_id>[\d]+)(?:/char_error=(?P<char_error>[\d,]+))?(?:/player_error=(?P<player_error>[\d,]+))?/$',
        views.start_game,
        name='games_start_game'),

    # ex: .com/contract/confirm_attendance/110
    re_path(r'^confirm_attendance/(?P<attendance_id>[\d]+)/$', views.confirm_attendance, name='games_confirm_attendance'),

    # ex: .com/contract/confirm_attendance/110/y
    re_path(r'^confirm_attendance/(?P<attendance_id>[\d]+)/(?P<confirmed>[yn])/$', views.confirm_attendance, name='games_confirm_attendance'),

    # ex: .com/contract/end/110
    re_path(r'^end/(?P<game_id>[\d]+)/$', views.end_game, name='games_end_game'),

    # ex: .com/contract/110
    re_path(r'^(?P<game_id>[\d]+)/$', views.view_game, name='games_view_game'),
    re_path(r'^view/g/(?P<game_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='games:games_view_game', query_string=True, permanent=True)),

    # ex: .com/contract/cancel/110
    re_path(r'^cancel/(?P<game_id>[\d]+)/$', views.cancel_game, name='games_cancel_game'),

    # ex: .com/contract/invite/110
    re_path(r'^invite/(?P<game_id>[\d]+)/$', views.invite_players, name='games_invite_players'),

    # ex: .com/contract/accept/110
    re_path(r'^accept/(?P<game_id>[\d]+)/$', views.accept_invite, name='games_accept_invite'),

    # ex: .com/contract/decline/110
    re_path(r'^decline/(?P<game_id>[\d]+)/$', views.decline_invite, name='games_decline_invite'),

    # ex: .com/contract/looking-for-game/
    re_path(r'^looking-for-game/$', views.LookingForGame.as_view(), name='games_looking_for_game'),

    # ex: .com/contract/allocate_improvement/i/219
    re_path(r'^allocate_improvement/i/(?P<improvement_id>[\d]+)/$', views.allocate_improvement, name='games_allocate_improvement'),

    # ex: .com/contract/allocate_improvement
    re_path(r'^allocate_improvement/$', views.allocate_improvement_generic,
        name='games_allocate_improvement_generic'),

    path('move/create/c/<int:character_id>/', views.CreateMoveChar.as_view(), name='create_move_char'),
    path('move/create/p/<int:cell_id>/', views.CreateMoveCell.as_view(), name='create_move_cell'),
    path('move/edit/<int:move_id>/', views.EditMove.as_view(), name='edit_move'),
    path('move/<int:move_id>/', views.ViewMove.as_view(), name='view_move'),

    ##################
    # AJAX endpoints
    ##################
    re_path(r'^post/ajax/grant-element/e/(?P<element_id>[\d]+)/$', views.grant_element,
        name="games_grant_element"),
]