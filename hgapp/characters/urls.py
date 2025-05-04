from django.urls import path, re_path

from . import views
from django.views.generic.base import RedirectView

app_name = 'characters'
urlpatterns = [
    # ex: .com/contractor/view/c/110
    re_path(r'^(?P<character_id>[\d]+)/$', views.view_character, name='characters_view'),
    re_path(r'^(?P<character_id>[\d]+)/stock/$', views.view_character_stock, name='characters_view_stock'),
    re_path(r'^view/c/(?P<character_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='characters:characters_view', query_string=True, permanent=True)),
    # ex: .com/contractor/view/c/110/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    re_path(r'^(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.view_character, name='characters_view'),
    re_path(r'^view/c/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$',
        RedirectView.as_view(pattern_name='characters:characters_view', query_string=True, permanent=True)),

    # ex: .com/contractor/view-contacts/110
    re_path(r'^view-contacts/(?P<character_id>[\d]+)/$', views.view_character_contacts, name='characters_view_contacts'),

    # ex: .com/contractor/reward/110
    re_path(r'^reward/(?P<character_id>[\d]+)/$', views.spend_reward, name='characters_spend_reward'),

    # ex: .com/contractor/download-txt/110
    re_path(r'^download-txt/(?P<character_id>[\d]+)/$', views.archive_character, name='characters_archive'),

    # ex: .com/contractor/print/110
    re_path(r'^print/(?P<character_id>[\d]+)/$', views.print_character, name='characters_print'),

    # ex: .com/contractor/blank
    re_path(r'^blank/$', views.blank_sheet, name='characters_blank_sheet'),

    # ex: .com/contractor/create/
    re_path(r'^create/$', views.create_character, name='characters_create'),
    # ex: .com/contractor/create/in-playgroup/123
    re_path(r'^create/in-playgroup/(?P<cell_id>[\d]+)$', views.create_character, name='characters_create_world'),

    # ex: .com/contractor/view/a/110
    re_path(r'^artifact/(?P<artifact_id>[\d]+)/$', views.view_artifact, name='characters_artifact_view'),
    re_path(r'^view/a/(?P<artifact_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='characters:characters_artifact_view', query_string=True, permanent=True)),

    # ex: .com/contractor/graveyard/
    re_path(r'^graveyard/$', views.graveyard, name='characters_graveyard'),

    # ex: .com/contractor/edit/112
    re_path(r'^edit/(?P<character_id>[\d]+)/$', views.edit_character, name='characters_edit'),
    # ex: .com/contractor/edit/112/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    re_path(r'^edit/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.edit_character, name='characters_edit'),

    # ex: .com/contractor/delete/112
    re_path(r'^delete/(?P<character_id>[\d]+)/$', views.delete_character, name='characters_delete'),

    # ex: .com/contractor/obituary/112
    re_path(r'^obituary/(?P<character_id>[\d]+)/$', views.edit_obituary, name='characters_obituary'),
    re_path(r'^obituary/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.edit_obituary, name='characters_obituary'),

    # ex: .com/contractor/assign-gifts/112/
    re_path(r'^assign-gifts/(?P<character_id>[\d]+)/$', views.choose_powers, name='characters_power_picker'),

    # ex: .com/contractor/gm/reward/
    re_path(r'^gm/reward/$', views.allocate_gm_exp, name='characters_allocate_gm_exp'),

    # ex: .com/contractor/edit/c/112/p/21
    re_path(r'^edit/c/(?P<character_id>[\d]+)/p/(?P<power_full_id>[\d]+)$', views.toggle_power, name='characters_power_toggle'),

    # ex: .com/contractor/edit/c/112/i/21
    re_path(r'^edit/c/(?P<character_id>[\d]+)/i/(?P<sig_artifact_id>[\d]+)$', views.toggle_item,
        name='characters_item_toggle'),

    # ex: .com/contractor/claim/112/6db20aef104038d363eca31985142c08daa82be57e29e53ad3c8171b9d46083f
    re_path(r'^claim/(?P<character_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.claim_character, name='characters_claim'),

    path('loose-end/create/<int:character_id>/', views.CreateLooseEnd.as_view(), name='create_loose_end'),
    path('loose-end/edit/l/<int:loose_end_id>/', views.EditLooseEnd.as_view(), name='edit_loose_end'),
    re_path(r'^loose-end/delete/l/(?P<loose_end_id>[\d]+)$', views.delete_loose_end, name='delete_loose_end'),

    #####
    # AJAX endpoints for character view page
    ######
    re_path(r'^get/ajax/item-timeline/(?P<artifact_id>[\d]+)/$', views.item_timeline, name="item_timeline"),
    re_path(r'^get/ajax/timeline/(?P<character_id>[\d]+)/$', views.character_timeline, name="character_timeline"),

    re_path(r'^post/ajax/transfer/a/(?P<artifact_id>[\d]+)/$', views.transfer_artifact, name="transfer_artifact"),

    re_path(r'^post/ajax/use-consumable/a/(?P<artifact_id>[\d]+)/$', views.use_consumable, name="use_consumable"),

    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/scar/$', views.post_scar, name="post_scar"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/scar/(?P<secret_key>[\da-z]*)$', views.post_scar, name="post_scar"),

    re_path(r'^post/ajax/delete-scar/s/(?P<scar_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.delete_scar,
        name="delete_scar"),
    re_path(r'^post/ajax/delete-scar/s/(?P<scar_id>[\d\w]+)/$', views.delete_scar, name="delete_scar"),

    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/equipment/(?P<secret_key>[\da-z]*)$', views.post_equipment, name="post_equipment"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/equipment/$', views.post_equipment, name="post_equipment"),

    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/bio/(?P<secret_key>[\da-z]*)$', views.post_bio,
        name="post_bio"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/bio/$', views.post_bio, name="post_bio"),

    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/notes/(?P<secret_key>[\da-z]*)$', views.post_notes,
        name="post_notes"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/notes/$', views.post_notes, name="post_notes"),

    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/trauma/(?P<secret_key>[\da-z]*)$', views.post_trauma, name="post_trauma"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/trauma/$', views.post_trauma, name="post_trauma"),

    re_path(r'^post/ajax/delete-trauma/s/(?P<trauma_rev_id>[\d\w]+)/xp/(?P<used_xp>[TF\w]*)/(?P<secret_key>[\da-z]*)$', views.delete_trauma, name="delete_trauma"),
    re_path(r'^post/ajax/delete-trauma/s/(?P<trauma_rev_id>[\d\w]+)/xp/(?P<used_xp>[TF\w]*)/$', views.delete_trauma, name="delete_trauma"),

    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/injury/$', views.post_injury, name="post_injury"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/injury/(?P<secret_key>[\da-z]*)$', views.post_injury,
        name="post_injury"),

    re_path(r'^post/ajax/dec-injury/s/(?P<injury_id>[\d\w]+)/$', views.dec_injury, name="dec_injury"),
    re_path(r'^post/ajax/dec-injury/s/(?P<injury_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.dec_injury,
        name="dec_injury"),
    re_path(r'^post/ajax/inc-injury/s/(?P<injury_id>[\d\w]+)/$', views.inc_injury, name="inc_injury"),
    re_path(r'^post/ajax/inc-injury/s/(?P<injury_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.inc_injury,
        name="inc_injury"),
    re_path(r'^post/ajax/stabilize-injury/s/(?P<injury_id>[\d\w]+)/$', views.stabilize_injury, name="stabilize_injury"),
    re_path(r'^post/ajax/stabilize-injury/s/(?P<injury_id>[\d\w]+)/(?P<secret_key>[\da-z]*)$', views.stabilize_injury,
        name="stabilize_injury"),

    # Sets character's mental damage to requested value in "severity" field of injury form. If out of bounds,
    # sets character's injury to either their number of mental health levels or 0.
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/mental/(?P<secret_key>[\da-z]*)$', views.set_mind_damage, name="set_mind_damage"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/mental/$', views.set_mind_damage, name="set_mind_damage"),

    # Sets source's current value to requested value. If out of bounds,
    # sets source value to either its max or 0.
    re_path(r'^post/ajax/update-source/s/(?P<source_id>[\d]+)/$', views.set_source_val, name="set_source_val"),
    re_path(r'^post/ajax/update-source/s/(?P<source_id>[\d]+)/(?P<secret_key>[\da-z]*)$', views.set_source_val,
        name="set_source_val"),

    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/world-element/(?P<element>[\w]+)/$',
        views.post_world_element,
        name="post_world_element"),
    re_path(r'^post/ajax/c/(?P<character_id>[\d]+)/world-element/(?P<element>[\w]+)/(?P<secret_key>[\da-z]*)$',
        views.post_world_element,
        name="post_world_element"),
    re_path(r'^post/ajax/c/(?P<element_id>[\d\w]+)/del-world-element/(?P<element>[\w]+)/$',
        views.delete_world_element,
        name="delete_world_element"),
    re_path(r'^post/ajax/c/(?P<element_id>[\d\w]+)/del-world-element/(?P<element>[\w]+)/(?P<secret_key>[\da-z]*)$',
        views.delete_world_element,
        name="delete_world_element"),
    re_path(r'^post/ajax/c/(?P<element_id>[\d\w]+)/edit-world-element/(?P<element>[\w]+)/$',
        views.edit_world_element,
        name="edit_world_element"),
    re_path(r'^post/ajax/c/(?P<element_id>[\d\w]+)/edit-world-element/(?P<element>[\w]+)/(?P<secret_key>[\da-z]*)$',
        views.edit_world_element,
        name="edit_world_element"),

    path('upload-image/<int:character_id>/', views.upload_image, name='characters_upload_image'),
    path('delete-image/<int:character_id>/<int:image_id>/', views.delete_image, name='characters_delete_image'),
    path('make-primary-image/<int:character_id>/<int:image_id>/', views.make_primary_image, name='characters_make_primary_image'),
]