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

@register.inclusion_tag('scenario_title.html')
def render_scenario_title_without_link(scenario, custom_link=None):
    return {
        "scenario": scenario,
        "render_link": False,
        "custom_link": custom_link,
    }

@register.inclusion_tag('scenario_title.html', takes_context=True)
def render_scenario_title_check_for_link(context, scenario):
    request = context["request"] if "request" in context else None
    if not request:
        raise ValueError("Scenario tag had no context")
    return {
        "scenario": scenario,
        "render_link": scenario.player_discovered(request.user),
    }


@register.inclusion_tag('scenario_title.html')
def render_scenario_title_with_link(scenario):
    return {
        "scenario": scenario,
        "render_link": True,
    }

@register.inclusion_tag('games/moves/move_badge.html', takes_context=True)
def render_move(context, move, gm_display=True):
    request = context["request"] if "request" in context else None
    if not request:
        raise ValueError("Scenario tag had no context")
    return {
        "move": move,
        "render_link": move.main_character.player_can_view(request.user),
        "gm_display": gm_display,
    }
