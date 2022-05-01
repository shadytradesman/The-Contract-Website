from django import template

register = template.Library()

@register.simple_tag
def player_can_edit_power(power, player):
    return power.parent_power.player_can_edit(player)

@register.inclusion_tag('powers/power_badge_snippet.html')
def discovery_power_badge(power_full):
    latest_revision = power_full.latest_revision()
    character = power_full.character if power_full.character else None
    return {
        'discovery_page': True,
        'power_full': power_full,
        'latest_revision': latest_revision,
        'character': character,
        'show_status_warning': False,
    }

@register.inclusion_tag('powers/power_badge_snippet.html')
def power_rev_badge(power, force_show_warnings=False, crafter_blurb=None, artifact=None):
    power_full = power.parent_power
    character = power_full.character if power_full.character else None
    show_status_warning = force_show_warnings
    if character:
        show_status_warning = not power.passes_status_check(character.status)
    show_active_toggle = power.show_status_toggle(artifact)
    is_active = show_active_toggle
    if show_active_toggle:
        is_active = power.get_is_active(artifact)
    art_id = artifact.id if artifact else None
    return {
        'discovery_page': False,
        'force_show_warnings': force_show_warnings,
        'power_full': power_full,
        'latest_revision': power,
        'character': character,
        'show_status_warning': show_status_warning,
        'crafter_blurb': crafter_blurb,
        'show_active_toggle': show_active_toggle,
        'is_active': is_active,
        'art_id': art_id,
    }

@register.inclusion_tag('powers/power_badge_snippet.html')
def power_badge(power_full, force_show_warnings=False, artifact=None):
    latest_revision = power_full.latest_revision()
    character = power_full.character if power_full.character else None
    show_status_warning = force_show_warnings
    if character:
        show_status_warning = not latest_revision.passes_status_check(character.status)
    show_active_toggle = latest_revision.show_status_toggle(artifact)
    is_active = show_active_toggle
    if show_active_toggle:
        is_active = latest_revision.get_is_active(artifact)
    art_id = artifact.id if artifact else None
    return {
        'discovery_page': False,
        'force_show_warnings': force_show_warnings,
        'power_full': power_full,
        'latest_revision': latest_revision,
        'character': character,
        'show_status_warning': show_status_warning,
        'show_active_toggle': show_active_toggle,
        'is_active': is_active,
        'art_id': art_id,
    }

@register.inclusion_tag('powers/ps2_view_pages/heading_snip.html')
def power_heading(power):
    latest_revision = power
    power_full = power.parent_power
    character = power_full.character if power_full.character else None
    show_status_warning = False
    if character:
        show_status_warning = not latest_revision.passes_status_check(character.status)
    return {
        'discovery_page': False,
        'power_full': power_full,
        'latest_revision': latest_revision,
        'show_status_warning': show_status_warning,
    }
