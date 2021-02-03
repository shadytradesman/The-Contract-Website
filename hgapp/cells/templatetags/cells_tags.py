from django import template
from .. import models

register = template.Library()

@register.simple_tag
def player_rank(cell, player):
    return models.CellMembership.objects.filter(relevant_cell=cell, member_player=player).first().get_role_display()

@register.simple_tag
def num_games_player_participated(cell, player):
    return cell.num_games_player_participated(player)