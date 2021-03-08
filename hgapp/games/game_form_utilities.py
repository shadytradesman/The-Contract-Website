from datetime import datetime
import pytz

from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User

from .models import Scenario, Game, DISCOVERY_REASON, Game_Invite, Game_Attendance, Reward
from .games_constants import GAME_STATUS

def convert_to_localtime(utctime):
  utc = utctime.replace(tzinfo=pytz.UTC)
  localtz = utc.astimezone(timezone.get_current_timezone())
  return localtz

def change_time_to_current_timezone(input_datetime):
    # Get the MODERN version of our timezone
    # https://stackoverflow.com/questions/35462876/python-pytz-timezone-function-returns-a-timezone-that-is-off-by-9-minutes
    time = datetime.now(timezone.get_current_timezone())
    return input_datetime.replace(tzinfo=time.tzinfo)

def get_context_for_create_finished_game(player_list, players, gm, cell, GenInfoForm, ArchivalOutcomeFormset):
    general_form = GenInfoForm(prefix="general")
    outcome_formset = ArchivalOutcomeFormset(prefix="outcome",
                                             initial=[{'player_id': x.id,
                                                       'invited_player': x}
                                                      for x in player_list])
    return {
        'general_form': general_form,
        'outcome_formset': outcome_formset,
        'cell': cell,
        'cell_id': cell.id,
        'gm_user_id': gm.id,
        'players': players,
        'gm': gm,
    }

def create_archival_game(request, general_form, cell, outcome_formset):
    form_gm = get_object_or_404(User, id=general_form.cleaned_data['gm_id'])
    if not cell.get_player_membership(form_gm):
        raise PermissionDenied("Only players who are members of a Cell can GM games inside it.")
    with transaction.atomic():
        occurred_time = general_form.cleaned_data['occurred_time']
        if "timezone" in general_form.cleaned_data:
            account = request.user.account
            account.timezone = general_form.cleaned_data["timezone"]
            account.save()
            occurred_time = change_time_to_current_timezone(occurred_time)
        # TODO: check to see if the game has the exact same time as existing game and fail.
        game = Game(
            title=general_form.cleaned_data['title'],
            creator=request.user,
            gm=form_gm,
            created_date=timezone.now(),
            scheduled_start_time=occurred_time,
            actual_start_time=occurred_time,
            end_time=occurred_time,
            status=GAME_STATUS[6][0],
            cell=cell,
        )
        if general_form.cleaned_data['scenario']:
            game.scenario = general_form.cleaned_data['scenario']
        game.save()
        for form in outcome_formset:
            player = get_object_or_404(User, id=form.cleaned_data['player_id'])
            attendance = Game_Attendance(
                relevant_game=game,
                notes=form.cleaned_data['notes'],
                outcome=form.cleaned_data['outcome'],
            )
            game_invite = Game_Invite(invited_player=player,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            game_invite.save()
            if 'attending_character' in form.cleaned_data \
                    and not form.cleaned_data['attending_character'] is None:
                if hasattr(form.cleaned_data['attending_character'], 'cell'):
                    attendance.attending_character = form.cleaned_data['attending_character']
                    if not form.cleaned_data['attending_character'].cell == cell:
                        attendance.is_confirmed = False
                else:
                    attendance.is_confirmed = False
            else:
                game_invite.as_ringer = True
                attendance.is_confirmed = False
            if game.creator.id == player.id:
                attendance.is_confirmed = True
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
        game.give_rewards()