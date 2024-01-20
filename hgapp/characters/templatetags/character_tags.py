from django import template

from characters.forms import make_world_element_form, make_transfer_artifact_form, make_artifact_status_form, \
    make_consumable_use_form
from characters.models import LOST, DESTROYED, RECOVERED, REPAIRED, AT_HOME, LOOSE_END
from django.urls import reverse
from django.template.loader import render_to_string

from collections import defaultdict
register = template.Library()

@register.inclusion_tag('characters/view_pages/consumable_item_snip.html',takes_context=True)
def render_consumable(context, artifact, user):
    request = context["request"] if "request" in context else None
    if not artifact.is_consumable:
        raise ValueError("attempting to display non-consumable artifact as consumable")
    can_use = artifact.character.player_can_edit(user)
    power = artifact.power_set.select_related("modality").select_related("vector").select_related("base").first()
    use_form = None
    transfer_form = None
    if can_use:
        use_form = make_consumable_use_form(artifact)
        transfer_form = make_transfer_artifact_form(artifact.character, artifact.character.cell, artifact.quantity)
    status_blurb = artifact.get_status_blurb()

    return {
        "artifact": artifact,
        "user": user,
        "can_use": can_use,
        "use_form": use_form,
        "transfer_form": transfer_form,
        "power": power,
        "crafter_blurb": status_blurb,
        "request": request,
    }


@register.inclusion_tag('characters/view_pages/sig_item_snip.html', takes_context=True)
def render_sig_item(context, artifact, user, viewing_character=None, rewarding_character=None, is_stock=False, is_preview=False):
    request = context["request"] if "request" in context else None
    if not (artifact.is_signature or artifact.is_crafted_artifact):
        raise ValueError("attempting to display non-signature artifact as signature")
    can_edit = artifact.player_can_edit_or_transfer(user)
    can_edit_gifts = artifact.player_can_edit_gifts(user)
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
    is_greyed_out = False
    if viewing_character:
        is_greyed_out = is_lost_or_destroyed or artifact.character != viewing_character
    if not is_stock:
        status_blurb = artifact.get_status_blurb()
    else:
        status_blurb = None
    reason_unavail = None
    if artifact.most_recent_status_change and artifact.most_recent_status_change not in [RECOVERED, REPAIRED]:
        reason_unavail = 'Currently {}.'.format(artifact.get_most_recent_status_change_display())
    render_link = viewing_character is not None
    events = artifact.craftingevent_set.all().order_by("id").reverse() #We can have multiple versions of one gift on an artifact.  We only want to show the newest (highest ID)
    powers_by_crafter = defaultdict(list)
    powers_by_parent_id = defaultdict(list)

    for event in events:
        if event.relevant_power.parent_power_id not in powers_by_parent_id:
            powers_by_crafter[event.relevant_character].append(event.relevant_power)
            powers_by_parent_id[event.relevant_power.parent_power_id] = event.relevant_power

    is_early_access = user.profile.early_access_user if user.is_authenticated else False,
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
        "powers_by_crafter": dict(powers_by_crafter),
        "can_edit_gifts": can_edit_gifts,
        "is_early_access": is_early_access,
        "request": request,
    }

