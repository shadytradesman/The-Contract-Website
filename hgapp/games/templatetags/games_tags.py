from django import template

register = template.Library()

@register.inclusion_tag('reward_thumb.html')
def render_reward(reward):
    return {
        'reward': reward,
    }

@register.inclusion_tag('gm_title.html')
def render_gm_title(player):
    return {
        'gm': player,
    }

@register.inclusion_tag('game_mediums.html')
def render_game_mediums(game):
    return {
        'game': game,
    }
