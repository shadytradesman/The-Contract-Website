from django.conf.urls import url

from . import views
from django.views.generic.base import RedirectView


app_name = 'cells'
urlpatterns = [
    # ex: .com/playgroup/create/
    url(r'^create/$', views.EditWorld.as_view(), name='cells_create'),

    # ex: .com/playgroup/edit/123
    url(r'^edit/(?P<cell_id>[\d]+)/$', views.EditWorld.as_view(), name='cells_edit'),

    # ex: .com/playgroup/edit-find-world/123
    url(r'^edit-find-world/(?P<cell_id>[\d]+)/$', views.EditFindWorld.as_view(), name='cells_edit_find_world'),

    # ex: .com/playgroup/123
    url(r'^(?P<cell_id>[\d]+)/$', views.view_cell, name='cells_view_cell'),
    url(r'^view/c/(?P<cell_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='cells:cells_view_cell', query_string=True)),

    # ex: .com/playgroup/invite/123
    url(r'^invite/(?P<cell_id>[\d]+)/$', views.invite_players, name='cells_invite_players'),

    # ex: .com/playgroup/post-event/123
    url(r'^post-event/(?P<cell_id>[\d]+)/$', views.PostWorldEvent.as_view(), name='cells_post_world_event'),
    # ex: .com/playgroup/post-event/123/event-id/32/
    url(r'^post-event/(?P<cell_id>[\d]+)/event-id/(?P<world_event_id>[\d]+)$', views.PostWorldEvent.as_view(), name='cells_edit_world_event'),

    # ex: .com/playgroup/invite/123/link-reset
    url(r'^invite/(?P<cell_id>[\d]+)/link-reset/$', views.reset_invite_link, name='cells_reset_invite_link'),

    # ex: .com/playgroup/invite/123/revoke/i/2352
    url(r'^invite/(?P<cell_id>[\d]+)/revoke/i/(?P<invite_id>[\d]+)$', views.revoke_invite, name='cells_revoke_invite'),

    # ex: .com/playgroup/invite/rsvp/123
    url(r'^invite/rsvp/(?P<cell_id>[\d]+)/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/playgroup/invite/rsvp/123/y
    url(r'^invite/rsvp/(?P<cell_id>[\d]+)/(?P<accept>[yn])/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/playgroup/invite/rsvp/123/code/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    url(r'^invite/rsvp/(?P<cell_id>[\d]+)/code/(?P<secret_key>[\da-z]+)/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/playgroup/invite/rsvp/123/code/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f/n
    url(r'^invite/rsvp/(?P<cell_id>[\d]+)/code/(?P<secret_key>[\da-z]+)/(?P<accept>[yn])$', views.rsvp_invite,
        name='cells_rsvp_invite'),

    # ex: .com/playgroup/members/123
    url(r'^members/(?P<cell_id>[\d]+)/$', views.manage_members, name='cells_manage_members'),

    # ex: .com/playgroup/webhooks/123
    url(r'^webhooks/(?P<cell_id>[\d]+)/$', views.manage_webhooks, name='cells_manage_webhooks'),

    # ex: .com/playgroup/roles/123
    url(r'^roles/(?P<cell_id>[\d]+)/$', views.ManageRoles.as_view(), name='cells_manage_roles'),

    # ex: .com/playgroup/kick/123/u/4141
    url(r'^kick/(?P<cell_id>[\d]+)/u/(?P<user_id>[\d]+)/$', views.kick_player, name='cells_kick_player'),

    # ex: .com/playgroup/kick/123/u/4141
    url(r'^ban/(?P<cell_id>[\d]+)/u/(?P<user_id>[\d]+)/$', views.ban_player, name='cells_ban_player'),

    # ex: .com/playgroup/leave/123
    url(r'^leave/(?P<cell_id>[\d]+)/$', views.leave_cell, name='cells_leave_cell'),

    # ex: .com/playgroup/find
    url(r'^find/$', views.FindWorld.as_view(), name='cells_find_world'),
]
