from django.conf.urls import url

from . import views

app_name = 'characters'
urlpatterns = [
    # ex: .com/characters/view/c/110
    url(r'^view/c/(?P<character_id>[\d]+)/$', views.view_character, name='characters_view'),

    # ex: .com/characters/reward/c/110
    url(r'^reward/c/(?P<character_id>[\d]+)/$', views.spend_reward, name='characters_spend_reward'),

    # ex: .com/characters/archive/c/110
    url(r'^archive/c/(?P<character_id>[\d]+)/$', views.archive_character, name='characters_archive'),

    # ex: .com/characters/create/
    url(r'^create/$', views.create_character, name='characters_create'),

    # ex: .com/characters/create/
    url(r'^graveyard/$', views.graveyard, name='characters_graveyard'),

    # ex: .com/characters/edit/c/112
    url(r'^edit/c/(?P<character_id>[\d]+)/$', views.edit_character, name='characters_edit'),

    # ex: .com/characters/obituary/c/112
    url(r'^obituary/c/(?P<character_id>[\d]+)/$', views.edit_obituary, name='characters_obituary'),

    # ex: .com/characters/edit/powers/c/112/
    url(r'^edit/powers/c/(?P<character_id>[\d]+)/$', views.choose_powers, name='characters_power_picker'),

    # ex: .com/characters/edit/c/112/p/21
    url(r'^edit/c/(?P<character_id>[\d]+)/p/(?P<power_full_id>[\d]+)$', views.toggle_power, name='characters_power_toggle'),

    # ex:
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/scar', views.post_scar, name="post_scar"),

    # ex:
    url(r'^post/ajax/delete-scar/s/(?P<scar_id>[\d\w]+)', views.delete_scar, name="delete_scar"),
]