from django.urls import re_path

from . import views
from django.views.generic.base import RedirectView


app_name = 'cells'
urlpatterns = [
    # ex: .com/playgroup/create/
    re_path(r'^create/$', views.EditWorld.as_view(), name='cells_create'),

    # ex: .com/playgroup/edit/123
    re_path(r'^edit/(?P<cell_id>[\d]+)/$', views.EditWorld.as_view(), name='cells_edit'),

    # ex: .com/playgroup/edit-find-world/123
    re_path(r'^edit-find-world/(?P<cell_id>[\d]+)/$', views.EditFindWorld.as_view(), name='cells_edit_find_world'),

    # ex: .com/playgroup/123
    re_path(r'^(?P<cell_id>[\d]+)/$', views.view_cell, name='cells_view_cell'),
    re_path(r'^view/c/(?P<cell_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='cells:cells_view_cell', query_string=True, permanent=True)),

    re_path(r'^contracts/(?P<cell_id>[\d]+)/$', views.view_cell_contracts, name='cell_contracts'),
    re_path(r'^community/(?P<cell_id>[\d]+)/$', views.view_cell_community, name='cell_community'),

    # ex: .com/playgroup/world-events/123
    re_path(r'^(?P<cell_id>[\d]+)/world-events/$', views.view_cell_events, name='cells_world_events'),

    # ex: .com/playgroup/invite/123
    re_path(r'^invite/(?P<cell_id>[\d]+)/$', views.invite_players, name='cells_invite_players'),

    # ex: .com/playgroup/post-event/123
    re_path(r'^post-event/(?P<cell_id>[\d]+)/$', views.PostWorldEvent.as_view(), name='cells_post_world_event'),
    # ex: .com/playgroup/post-event/123/event-id/32/
    re_path(r'^post-event/(?P<cell_id>[\d]+)/event-id/(?P<world_event_id>[\d]+)$', views.PostWorldEvent.as_view(), name='cells_edit_world_event'),

    # ex: .com/playgroup/invite/123/link-reset
    re_path(r'^invite/(?P<cell_id>[\d]+)/link-reset/$', views.reset_invite_link, name='cells_reset_invite_link'),

    # ex: .com/playgroup/invite/123/revoke/i/2352
    re_path(r'^invite/(?P<cell_id>[\d]+)/revoke/i/(?P<invite_id>[\d]+)$', views.revoke_invite, name='cells_revoke_invite'),

    # ex: .com/playgroup/invite/rsvp/123
    re_path(r'^invite/rsvp/(?P<cell_id>[\d]+)/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/playgroup/invite/rsvp/123/c/21
    re_path(r'^invite/rsvp/(?P<cell_id>[\d]+)/c/(?P<game_id>[\d]+)/$', views.rsvp_invite, name='cells_rsvp_invite_contract'),

    # ex: .com/playgroup/invite/rsvp/123/c/21/y
    re_path(r'^invite/rsvp/(?P<cell_id>[\d]+)/c/(?P<game_id>[\d]+)/(?P<accept>[yn])/$', views.rsvp_invite, name='cells_rsvp_invite_contract'),

    # ex: .com/playgroup/invite/rsvp/123/y
    re_path(r'^invite/rsvp/(?P<cell_id>[\d]+)/(?P<accept>[yn])/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/playgroup/invite/rsvp/123/code/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    re_path(r'^invite/rsvp/(?P<cell_id>[\d]+)/code/(?P<secret_key>[\da-z]+)/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/playgroup/invite/rsvp/123/code/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f/n
    re_path(r'^invite/rsvp/(?P<cell_id>[\d]+)/code/(?P<secret_key>[\da-z]+)/(?P<accept>[yn])$', views.rsvp_invite,
        name='cells_rsvp_invite'),

    # ex: .com/playgroup/add-contractors/123/
    re_path(r'^add-contractors/(?P<cell_id>[\d]+)/$', views.add_characters, name='add_characters_to_cell'),

    # ex: .com/playgroup/add-contractors/123/341
    re_path(r'^add-contractors/(?P<cell_id>[\d]+)/(?P<game_id>[\d]+)/$', views.add_characters, name='add_characters_to_cell'),

    # ex: .com/playgroup/members/123
    re_path(r'^members/(?P<cell_id>[\d]+)/$', views.manage_members, name='cells_manage_members'),

    # ex: .com/playgroup/webhooks/123
    re_path(r'^webhooks/(?P<cell_id>[\d]+)/$', views.manage_webhooks, name='cells_manage_webhooks'),

    # ex: .com/playgroup/roles/123
    re_path(r'^roles/(?P<cell_id>[\d]+)/$', views.ManageRoles.as_view(), name='cells_manage_roles'),

    # ex: .com/playgroup/kick/123/u/4141
    re_path(r'^kick/(?P<cell_id>[\d]+)/u/(?P<user_id>[\d]+)/$', views.kick_player, name='cells_kick_player'),

    # ex: .com/playgroup/kick/123/u/4141
    re_path(r'^ban/(?P<cell_id>[\d]+)/u/(?P<user_id>[\d]+)/$', views.ban_player, name='cells_ban_player'),

    # ex: .com/playgroup/leave/123
    re_path(r'^leave/(?P<cell_id>[\d]+)/$', views.leave_cell, name='cells_leave_cell'),

    # ex: .com/playgroup/find
    re_path(r'^find/$', views.FindWorld.as_view(), name='cells_find_world'),
]
