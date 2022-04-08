from django import template

from characters.forms import make_world_element_form, make_transfer_artifact_form, make_artifact_status_form
from characters.models import LOST, DESTROYED, RECOVERED, REPAIRED
from django.urls import reverse

register = template.Library()

@register.inclusion_tag('characters/view_pages/sig_item_snip.html', takes_context=True)
def render_sig_item(context, artifact, user, viewing_character=None):
    latest_transfer = artifact.get_latest_transfer()
    can_edit = artifact.character.player_can_edit(user)
    if can_edit:
        edit_form = make_world_element_form(for_new=False)()
        make_transfer_artifact_form(artifact.character, context["cell"] if "cell" in context else None)
        status_form = make_artifact_status_form(artifact.most_recent_status_change)
    is_lost_or_destroyed = artifact.most_recent_status_change and artifact.most_recent_status_change in [LOST, DESTROYED]
    is_held_by_creator = artifact.character == artifact.crafting_character
    is_greyed_out = False
    if viewing_character:
        is_greyed_out = is_lost_or_destroyed or artifact.character != viewing_character
    if is_held_by_creator:
        status_blurb = 'Created and held by <a href="{}">{}</a>.'.format(
            reverse('characters:characters_view', args=(artifact.crafting_character.id,)),
            artifact.crafting_character.name,)
    else:
        # if not held by creator, it should have a transfer.
        status_blurb = 'Created by <a href="{}">{}</a>, {} by <a href="{}">{}</a>.'.format(
            reverse('characters:characters_view', args=(artifact.crafting_character.id,)),
            artifact.crafting_character.name,
            latest_transfer.get_transfer_type_dispaly(),
            reverse('characters:characters_view', args=(artifact.character.id,)),
            artifact.character.name)
    reason_unavail = None
    if artifact.most_recent_status_change and artifact.most_recent_status_change not in [RECOVERED, REPAIRED]:
        reason_unavail = 'Currently {}.'.format(artifact.get_most_recent_status_change_display())
    return {
        "item": artifact,
        "user_can_edit": can_edit,
        "is_greyed_out": is_greyed_out,
        "status_blurb": status_blurb,
        "reason_unavail": reason_unavail,
        "edit_form": edit_form,
        "status_form": status_form,
    }

