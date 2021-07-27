from django import template
from django.db.models import Prefetch

from powers.models import Power, Enhancement_Instance

register = template.Library()

@register.simple_tag
def player_can_edit_power(power, player):
    return power.parent_power.player_can_edit(player)


@register.inclusion_tag('powers/power_badge_snippet.html')
def power_badge(power_full):
    latest_revision = power_full.latest_revision()
    latest_revision = Power.objects.filter(pk=latest_revision.pk) \
        .prefetch_related(
            Prefetch(
                'selected_enhancements',\
                queryset=Enhancement_Instance.objects\
                    .select_related('relevant_enhancement'),
                )\
            )\
        .first()
    # .select_related('base')\
    # .select_related('created_by') \
        # .prefetch_related('selected_enhancements') \
        # .prefetch_related('selected_drawbacks') \
        # .prefetch_related('parameter_values')\
    return {
        'power_full': power_full,
        'latest_revision': latest_revision,
    }
