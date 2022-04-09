from django.conf.urls import url

from . import views

app_name = 'characters'
urlpatterns = [
    # ex: .com/characters/view/c/110
    url(r'^view/c/(?P<character_id>[\d]+)/$', views.view_character, name='characters_view'),
    # ex: .com/characters/view/c/110/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    url(r'^view/c/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.view_character, name='characters_view'),

    # ex: .com/characters/view-contacts/c/110
    url(r'^view-contacts/c/(?P<character_id>[\d]+)/$', views.view_character_contacts, name='characters_view_contacts'),

    # ex: .com/characters/reward/c/110
    url(r'^reward/c/(?P<character_id>[\d]+)/$', views.spend_reward, name='characters_spend_reward'),

    # ex: .com/characters/archive/c/110
    url(r'^archive/c/(?P<character_id>[\d]+)/$', views.archive_character, name='characters_archive'),

    # ex: .com/characters/create/
    url(r'^create/$', views.create_character, name='characters_create'),
    # ex: .com/characters/create/world/123
    url(r'^create/world/(?P<cell_id>[\d]+)$', views.create_character, name='characters_create_world'),

    # ex: .com/characters/view/a/110
    url(r'^view/a/(?P<artifact_id>[\d]+)/$', views.view_artifact, name='characters_artifact_view'),

    # ex: .com/characters/graveyard/
    url(r'^graveyard/$', views.graveyard, name='characters_graveyard'),

    # ex: .com/characters/edit/c/112
    url(r'^edit/c/(?P<character_id>[\d]+)/$', views.edit_character, name='characters_edit'),
    # ex: .com/characters/edit/c/112/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    url(r'^edit/c/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.edit_character, name='characters_edit'),

    # ex: .com/characters/delete/c/112
    url(r'^delete/c/(?P<character_id>[\d]+)/$', views.delete_character, name='characters_delete'),

    # ex: .com/characters/obituary/c/112
    url(r'^obituary/c/(?P<character_id>[\d]+)/$', views.edit_obituary, name='characters_obituary'),
    url(r'^obituary/c/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.edit_obituary, name='characters_obituary'),

    # ex: .com/characters/edit/powers/c/112/
    url(r'^edit/powers/c/(?P<character_id>[\d]+)/$', views.choose_powers, name='characters_power_picker'),

    # ex: .com/characters/gm/reward/
    url(r'^gm/reward/$', views.allocate_gm_exp, name='characters_allocate_gm_exp'),

    # ex: .com/characters/edit/c/112/p/21
    url(r'^edit/c/(?P<character_id>[\d]+)/p/(?P<power_full_id>[\d]+)$', views.toggle_power, name='characters_power_toggle'),

    # ex: .com/characters/edit/c/112/i/21
    url(r'^edit/c/(?P<character_id>[\d]+)/i/(?P<sig_artifact_id>[\d]+)$', views.toggle_item,
        name='characters_item_toggle'),

    # ex: .com/characters/claim/c/112/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    url(r'^claim/c/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.claim_character, name='characters_claim'),

    #####
    # AJAX endpoints for character view page
    ######
    url(r'^get/ajax/item-timeline/(?P<artifact_id>[\d]+)/$', views.item_timeline, name="item_timeline"),
    url(r'^get/ajax/timeline/(?P<character_id>[\d]+)/$', views.character_timeline, name="character_timeline"),

    url(r'^post/ajax/transfer/a/(?P<artifact_id>[\d]+)/$', views.transfer_artifact, name="transfer_artifact"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/scar/$', views.post_scar, name="post_scar"),
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/scar/(?P<secret_key>[\da-z]*)$', views.post_scar, name="post_scar"),

    url(r'^post/ajax/delete-scar/s/(?P<scar_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.delete_scar,
        name="delete_scar"),
    url(r'^post/ajax/delete-scar/s/(?P<scar_id>[\d\w]+)/$', views.delete_scar, name="delete_scar"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/equipment/(?P<secret_key>[\da-z]*)$', views.post_equipment, name="post_equipment"),
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/equipment/$', views.post_equipment, name="post_equipment"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/bio/(?P<secret_key>[\da-z]*)$', views.post_bio,
        name="post_bio"),
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/bio/$', views.post_bio, name="post_bio"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/trauma/(?P<secret_key>[\da-z]*)$', views.post_trauma, name="post_trauma"),
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/trauma/$', views.post_trauma, name="post_trauma"),

    url(r'^post/ajax/delete-trauma/s/(?P<trauma_rev_id>[\d\w]+)/xp/(?P<used_xp>[TF\w]*)/(?P<secret_key>[\da-z]*)$', views.delete_trauma, name="delete_trauma"),
    url(r'^post/ajax/delete-trauma/s/(?P<trauma_rev_id>[\d\w]+)/xp/(?P<used_xp>[TF\w]*)/$', views.delete_trauma, name="delete_trauma"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/injury/$', views.post_injury, name="post_injury"),
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/injury/(?P<secret_key>[\da-z]*)$', views.post_injury,
        name="post_injury"),

    url(r'^post/ajax/dec-injury/s/(?P<injury_id>[\d\w]+)/$', views.dec_injury, name="dec_injury"),
    url(r'^post/ajax/dec-injury/s/(?P<injury_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.dec_injury,
        name="dec_injury"),
    url(r'^post/ajax/inc-injury/s/(?P<injury_id>[\d\w]+)/$', views.inc_injury, name="inc_injury"),
    url(r'^post/ajax/inc-injury/s/(?P<injury_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.inc_injury,
        name="inc_injury"),
    url(r'^post/ajax/stabilize-injury/s/(?P<injury_id>[\d\w]+)/$', views.stabilize_injury, name="stabilize_injury"),
    url(r'^post/ajax/stabilize-injury/s/(?P<injury_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.stabilize_injury,
        name="stabilize_injury"),

    # Sets character's mental damage to requested value in "severity" field of injury form. If out of bounds,
    # sets character's injury to either their number of mental health levels or 0.
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/mental/(?P<secret_key>[\da-z]*)$', views.set_mind_damage, name="set_mind_damage"),
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/mental/$', views.set_mind_damage, name="set_mind_damage"),

    # Sets source's current value to requested value. If out of bounds,
    # sets source value to either its max or 0.
    url(r'^post/ajax/update-source/s/(?P<source_id>[\d]+)/$', views.set_source_val, name="set_source_val"),
    url(r'^post/ajax/update-source/s/(?P<source_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.set_source_val,
        name="set_source_val"),

    url(r'^post/ajax/c/(?P<character_id>[\d]+)/world-element/(?P<element>[\w]+)/$',
        views.post_world_element,
        name="post_world_element"),
    url(r'^post/ajax/c/(?P<character_id>[\d]+)/world-element/(?P<element>[\w]+)/(?P<secret_key>[\da-z]*)$',
        views.post_world_element,
        name="post_world_element"),
    url(r'^post/ajax/c/(?P<element_id>[\d\w]+)/del-world-element/(?P<element>[\w]+)/$',
        views.delete_world_element,
        name="delete_world_element"),
    url(r'^post/ajax/c/(?P<element_id>[\d\w]+)/del-world-element/(?P<element>[\w]+)/(?P<secret_key>[\da-z]*)$',
        views.delete_world_element,
        name="delete_world_element"),
    url(r'^post/ajax/c/(?P<element_id>[\d\w]+)/edit-world-element/(?P<element>[\w]+)/$',
        views.edit_world_element,
        name="edit_world_element"),
    url(r'^post/ajax/c/(?P<element_id>[\d\w]+)/edit-world-element/(?P<element>[\w]+)/(?P<secret_key>[\da-z]*)$',
        views.edit_world_element,
        name="edit_world_element"),
]