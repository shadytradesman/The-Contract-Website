from django import template
from games.models import Game, GAME_STATUS, Game_Attendance
from games.games_constants import get_completed_game_excludes_query
import datetime

register = template.Library()

@register.simple_tag
def render_citizenship(player, cell):
    last_gm_game = Game.objects.filter(gm=player, cell=cell).exclude(get_completed_game_excludes_query()).order_by("-end_time").first()
    last_gm_game_time = datetime.datetime(1970, 1, 1, 0, 0) if last_gm_game is None else last_gm_game.end_time
    return player.profile.completed_game_invites().filter(relevant_game__cell=cell, relevant_game__end_time__gt=last_gm_game_time).count()


@register.inclusion_tag('games/view_game_pages/post_game_invite_tag.html')
def render_post_game_invite(game, invitation, player):
    attending_contractor = invitation.attendance.attending_character
    return {
        'game': game,
        'invitation': invitation,
        'contractor': attending_contractor,
        'player_can_view_contractor': attending_contractor.player_can_view(player) if attending_contractor else False,
        'player_can_edit_contractor': attending_contractor.player_can_edit(player) if attending_contractor else False,
        'reward': invitation.attendance.get_reward(),
    }

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


@register.inclusion_tag('scenario_unlock_button.html', takes_context=True)
def render_scenario_unlock(context, scenario):
    request = context["request"] if "request" in context else None
    if not request:
        raise ValueError("Scenario tag had no context")
    return {
        "scenario": scenario,
        "unlockable": not scenario.player_discovered(request.user),
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
