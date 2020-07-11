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

    #####
    # AJAX endpoints for character view page
    ######
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/scar', views.post_scar, name="post_scar"),

    url(r'^post/ajax/delete-scar/s/(?P<scar_id>[\d\w]+)', views.delete_scar, name="delete_scar"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/trauma', views.post_trauma, name="post_trauma"),

    url(r'^post/ajax/delete-trauma/s/(?P<trauma_rev_id>[\d\w]+)/xp/(?P<used_xp>[TF]*)', views.delete_trauma, name="delete_trauma"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/injury', views.post_injury, name="post_injury"),

    url(r'^post/ajax/delete-injury/s/(?P<injury_id>[\d\w]+)', views.delete_injury, name="delete_injury"),

    # Sets character's mental damage to requested value in "severity" field of injury form. If out of bounds,
    # sets character's injury to either their number of mental health levels or 0.
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/mental', views.set_mind_damage, name="set_mind_damage"),

    # Sets source's current value to requested value in "severity" field of injury form. If out of bounds,
    # sets character's injury to either their number of mental health levels or 0.
    url(r'^post/ajax/update-source/s/(?P<source_id>[\d]+)/', views.set_source_val, name="set_source_val"),

]