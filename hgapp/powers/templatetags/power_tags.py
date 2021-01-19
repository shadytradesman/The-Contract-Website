from django import template

register = template.Library()

@register.simple_tag
def player_can_edit_power(power, player):
    return power.parent_power.player_can_edit(player)