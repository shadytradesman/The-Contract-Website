from django import template

from powers.models import Power

register = template.Library()

@register.simple_tag
def player_can_edit_power(power, player):
    return power.parent_power.player_can_edit(player)


@register.inclusion_tag('powers/power_badge_snippet.html')
def power_badge(power_full):
    latest_revision = power_full.latest_revision()
    return {
        'power_full': power_full,
        'latest_revision': latest_revision,
    }
