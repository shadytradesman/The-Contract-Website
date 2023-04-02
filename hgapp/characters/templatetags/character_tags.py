from django import template

from characters.forms import make_world_element_form, make_transfer_artifact_form, make_artifact_status_form, \
    make_consumable_use_form
from characters.models import LOST, DESTROYED, RECOVERED, REPAIRED, AT_HOME, LOOSE_END
from django.urls import reverse
from django.template.loader import render_to_string

register = template.Library()

@register.inclusion_tag('characters/view_pages/consumable_item_snip.html')
def render_consumable(artifact, user):
    if not artifact.is_consumable:
        raise ValueError("attempting to display non-consumable artifact as consumable")
    can_use = artifact.character.player_can_edit(user)
    power = artifact.power_set.select_related("modality").select_related("vector").select_related("base").first()
    use_form = None
    transfer_form = None
    if can_use:
        use_form = make_consumable_use_form(artifact)
        transfer_form = make_transfer_artifact_form(artifact.character, artifact.character.cell, artifact.quantity)
    crafter_blurb = 'Crafted by <a href="{}">{}</a>'.format(
        reverse('characters:characters_view', args=(artifact.crafting_character.id,)),
        artifact.crafting_character.name)

    return {
        "artifact": artifact,
        "user": user,
        "can_use": can_use,
        "use_form": use_form,
        "transfer_form": transfer_form,
        "power": power,
        "crafter_blurb": crafter_blurb,
    }


@register.inclusion_tag('characters/view_pages/sig_item_snip.html')
def render_sig_item(artifact, user, viewing_character=None, rewarding_character=None, is_stock=False, is_preview=False):
    if not (artifact.is_signature or artifact.is_crafted_artifact):
        raise ValueError("attempting to display non-signature artifact as signature")
    latest_transfer = artifact.get_latest_transfer()
    can_edit = artifact.character.player_can_edit(user) if artifact.character else artifact.creating_player == user
    edit_form = None
    status_form = None
    transfer_form = None
    if can_edit and not is_stock and not is_preview:
        edit_form = make_world_element_form(for_new=False)()
        transfer_form = make_transfer_artifact_form(artifact.character if artifact.character else None,
                                                    artifact.character.cell if artifact.character else None,
                                                    user=user)
        status_form = make_artifact_status_form(artifact.most_recent_status_change)
    is_lost_or_destroyed = artifact.most_recent_status_change and artifact.most_recent_status_change in [LOST, AT_HOME, DESTROYED]
    is_held_by_creator = artifact.character and (artifact.character == artifact.crafting_character)
    is_greyed_out = False
    if viewing_character:
        is_greyed_out = is_lost_or_destroyed or artifact.character != viewing_character
    if not is_stock:
        if is_held_by_creator:
            status_blurb = 'Created and held by <a href="{}">{}</a>.'.format(
                reverse('characters:characters_view', args=(artifact.crafting_character.id,)),
                artifact.crafting_character.name,)
        elif artifact.crafting_character:
            # if not held by creator, it should have a transfer.
            status_blurb = 'Created by <a href="{}">{}</a>, {} <a href="{}">{}</a>.'.format(
                reverse('characters:characters_view', args=(artifact.crafting_character.id,)),
                artifact.crafting_character.name,
                latest_transfer.get_transfer_type_display(),
                reverse('characters:characters_view', args=(artifact.character.id,)),
                artifact.character.name)
        elif artifact.character:
            status_blurb = 'Created by <a href="{}">{}</a> and orphaned. Held by <a href="{}">{}</a>'.format(
                reverse('profiles:profiles_view_profile', args=(artifact.creating_player.id,)),
                artifact.creating_player.username,
                reverse('characters:characters_view', args=(artifact.character.id,)),
                artifact.character.name)
        elif artifact.creating_player:
            status_blurb = 'Created by <a href="{}">{}</a> and orphaned.'.format(
                reverse('profiles:profiles_view_profile', args=(artifact.creating_player.id,)),
                artifact.creating_player.username)
        else:
            status_blurb = 'Created by an anonymous user.'.format()
    else:
        status_blurb = None
    reason_unavail = None
    if artifact.most_recent_status_change and artifact.most_recent_status_change not in [RECOVERED, REPAIRED]:
        reason_unavail = 'Currently {}.'.format(artifact.get_most_recent_status_change_display())
    render_link = viewing_character is not None
    return {
        "item": artifact,
        "is_crafted": artifact.is_crafted_artifact,
        "user_can_edit": can_edit,
        "is_greyed_out": is_greyed_out,
        "status_blurb": status_blurb,
        "reason_unavail": reason_unavail,
        "edit_form": edit_form,
        "status_form": status_form,
        "transfer_form": transfer_form,
        "render_link": render_link,
        "rewarding_character": rewarding_character,
        "is_stock": is_stock,
        "is_preview": is_preview,
    }

