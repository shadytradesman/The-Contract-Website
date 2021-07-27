from django import template

from powers.models import Power

register = template.Library()

@register.simple_tag
def player_can_edit_power(power, player):
    return power.parent_power.player_can_edit(player)


@register.inclusion_tag('powers/power_badge_snippet.html')
def power_badge(power_full):
    latest_revision = power_full.latest_revision()
    latest_revision = Power.objects.get(pk=latest_revision.pk) \
        .select_related('base')\
        .select_related('created_by')\
        .prefetch_related('selected_enhancements') \
        .prefetch_related('selected_enhancements__') \
        .prefetch_related('selected_drawbacks') \
        .prefetch_related('parameter_values')
    return {
        'power_full': power_full,
        'latest_revision': latest_revision,
    }
