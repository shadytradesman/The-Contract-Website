from django import template

register = template.Library()

@register.simple_tag
def player_can_edit_power(power, player):
    return power.parent_power.player_can_edit(player)


@register.inclusion_tag('powers/power_badge_snippet.html')
def power_badge(power_full):
    latest_revision = power_full.latest_revision()
    character = power_full.character if power_full.character else None
    show_status_warning = False
    if character:
        show_status_warning = not latest_revision.passes_status_check(character.status)
    return {
        'power_full': power_full,
        'latest_revision': latest_revision,
        'character': character,
        'show_status_warning': show_status_warning,
    }

@register.inclusion_tag('powers/ps2_view_pages/heading_snip.html')
def power_heading(power_full):
    latest_revision = power_full.latest_revision()
    return {
        'power_full': power_full,
        'latest_revision': latest_revision,
    }
