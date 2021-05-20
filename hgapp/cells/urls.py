from django.conf.urls import url

from . import views


app_name = 'cells'
urlpatterns = [
    # ex: .com/cells/create/
    url(r'^create/$', views.EditWorld.as_view(), name='cells_create'),

    # ex: .com/cells/edit/c/123
    url(r'^edit/c/(?P<cell_id>[\d]+)/$', views.EditWorld.as_view(), name='cells_edit'),

    # ex: .com/cells/edit/c/123
    url(r'^edit-find-world/c/(?P<cell_id>[\d]+)/$', views.EditFindWorld.as_view(), name='cells_edit_find_world'),

    # ex: .com/cells/view/c/123
    url(r'^view/c/(?P<cell_id>[\d]+)/$', views.view_cell, name='cells_view_cell'),

    # ex: .com/cells/invite/c/123
    url(r'^invite/c/(?P<cell_id>[\d]+)/$', views.invite_players, name='cells_invite_players'),

    # ex: .com/cells/post-event/c/123
    url(r'^post-event/c/(?P<cell_id>[\d]+)/$', views.PostWorldEvent.as_view(), name='cells_post_world_event'),
    # ex: .com/cells/post-event/c/123/event-id/32/
    url(r'^post-event/c/(?P<cell_id>[\d]+)/event-id/(?P<world_event_id>[\d]+)$', views.PostWorldEvent.as_view(), name='cells_edit_world_event'),

    # ex: .com/cells/invite/c/123/link-reset
    url(r'^invite/c/(?P<cell_id>[\d]+)/link-reset/$', views.reset_invite_link, name='cells_reset_invite_link'),

    # ex: .com/cells/invite/c/123/revoke/i/2352
    url(r'^invite/c/(?P<cell_id>[\d]+)/revoke/i/(?P<invite_id>[\d]+)$', views.revoke_invite, name='cells_revoke_invite'),

    # ex: .com/cells/invite/rsvp/c/123
    url(r'^invite/rsvp/c/(?P<cell_id>[\d]+)/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/cells/invite/rsvp/c/123/y
    url(r'^invite/rsvp/c/(?P<cell_id>[\d]+)/(?P<accept>[yn])/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/cells/invite/rsvp/c/123/code/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    url(r'^invite/rsvp/c/(?P<cell_id>[\d]+)/code/(?P<secret_key>[\da-z]+)/$', views.rsvp_invite, name='cells_rsvp_invite'),

    # ex: .com/cells/invite/rsvp/c/123/code/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f/n
    url(r'^invite/rsvp/c/(?P<cell_id>[\d]+)/code/(?P<secret_key>[\da-z]+)/(?P<accept>[yn])$', views.rsvp_invite,
        name='cells_rsvp_invite'),

    # ex: .com/cells/members/c/123
    url(r'^members/c/(?P<cell_id>[\d]+)/$', views.manage_members, name='cells_manage_members'),

    # ex: .com/cells/roles/c/123
    url(r'^roles/c/(?P<cell_id>[\d]+)/$', views.ManageRoles.as_view(), name='cells_manage_roles'),

    # ex: .com/cells/kick/c/123/p/4141
    url(r'^kick/c/(?P<cell_id>[\d]+)/u/(?P<user_id>[\d]+)/$', views.kick_player, name='cells_kick_player'),

    # ex: .com/cells/leave/c/123
    url(r'^leave/c/(?P<cell_id>[\d]+)/$', views.leave_cell, name='cells_leave_cell'),

    # ex: .com/cells/find
    url(r'^find/$', views.FindWorld.as_view(), name='cells_find_world'),
]
