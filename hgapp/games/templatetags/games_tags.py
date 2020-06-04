from django import template

register = template.Library()

@register.inclusion_tag('reward_thumb.html')
def render_reward(reward):
    return {
        'reward': reward,
    }
