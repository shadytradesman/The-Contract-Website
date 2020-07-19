from itertools import chain

from account.models import Account
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.conf import settings

# Create your views here.
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import assign_perm

from characters.models import Character
from powers.models import Power_Full

from games.models import GAME_STATUS


def home(request):
    if request.user.is_anonymous:
        return render(request, 'logged_out_homepage.html')
    else:
        my_characters = request.user.character_set.filter(is_deleted=False).order_by('name').all()
        my_powers = request.user.power_full_set.filter(is_deleted=False).order_by('name').all()
        my_scenarios = request.user.scenario_creator.order_by("title").all()
        new_players = User.objects.order_by('-date_joined')[:6]
        new_powers = Power_Full.objects.filter(private=False).order_by('-id')[:6]
        new_characters = Character.objects.filter(private=False).order_by('-id')[:6]
        upcoming_games_running = request.user.game_creator.filter(status=GAME_STATUS[0][0]).all()
        upcoming_games_invited = request.user.game_invite_set.filter(relevant_game__status=GAME_STATUS[0][0]).all()
        active_games_attending =  request.user.game_set.filter(status=GAME_STATUS[1][0])
        active_games_creator = request.user.game_creator.filter(status=GAME_STATUS[1][0])
        active_games = list(chain(active_games_attending, active_games_creator))
        avail_improvements = request.user.rewarded_player.filter(rewarded_character=None, is_charon_coin=False).filter(is_void=False).all()
        avail_charon_coins = request.user.rewarded_player.filter(rewarded_character=None, is_charon_coin=True).filter(is_void=False).all()
        cells = request.user.cell_set.all()
        cell_invites = request.user.cellinvite_set.filter(membership=None).filter(is_declined=False).all()
        attendance_invites_to_confirm = request.user.game_invite_set.filter(attendance__is_confirmed=False).exclude(is_declined=True).all()
        avail_exp_rewards = request.user.experiencereward_set.filter(rewarded_character=None).all()
        context = {
            'characters': my_characters,
            'powers': my_powers,
            'my_scenarios': my_scenarios,
            'new_players': new_players,
            'new_powers': new_powers,
            'new_characters': new_characters,
            'upcoming_games_running': upcoming_games_running,
            'upcoming_games_invited': upcoming_games_invited,
            'active_games': active_games,
            'avail_improvements': avail_improvements,
            'avail_charon_coins': avail_charon_coins,
            'cells': cells,
            'cell_invites': cell_invites,
            'attendance_invites_to_confirm': attendance_invites_to_confirm,
            'avail_exp_rewards': avail_exp_rewards,
        }
        return render(request, 'logged_in_homepage.html', context)
