from datetime import datetime
import pytz

from django.forms import formset_factory
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User

from .forms import make_archive_game_general_info_form, ArchivalOutcomeForm, CellMemberAttendedForm, OutsiderAttendedForm, \
    make_who_was_gm_form
from .models import Game, Game_Invite, Game_Attendance
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


def _get_outcome_formset_for_edit(game, new_player_list, POST=None):
    ArchivalOutcomeFormset = formset_factory(ArchivalOutcomeForm, extra=0)
    initial_existing = [{'player_id': attendance.get_player().id,
                         'attendance_id': attendance.id,
                         'invited_player': attendance.get_player(),
                         'attending_character': attendance.attending_character,
                         'outcome': attendance.outcome,
                         'notes': attendance.notes, } for attendance in game.game_attendance_set.all()]
    initial_new = [{'player_id': x.id, 'invited_player': x} for x in new_player_list]
    initial_outcomes = initial_existing + initial_new
    return ArchivalOutcomeFormset(POST,
                                 prefix="outcome",
                                 initial=initial_outcomes)


def get_context_for_completed_edit(game, new_player_list, new_player_ids):
    general_form = _get_general_completed_form_for_edit(game)
    outcome_formset = _get_outcome_formset_for_edit(game, new_player_list)
    return {
        'general_form': general_form,
        'outcome_formset': outcome_formset,
        'cell': game.cell,
        'cell_id': game.cell.id,
        'gm_user_id': game.gm.id,
        'players': new_player_ids,
        'gm': game.gm,
        'game': game,
    }

def handle_edit_completed_game(request, game, new_player_list):
    general_form = _get_general_completed_form_for_edit(game, request.POST)
    outcome_formset = _get_outcome_formset_for_edit(game, new_player_list, request.POST)
    if general_form.is_valid():
        if outcome_formset.is_valid():
            with transaction.atomic():
                original_game_ratio = game.achieves_golden_ratio()
                if "timezone" in general_form.changed_data or "occurred_time" in general_form.changed_data:
                    occurred_time = general_form.cleaned_data['occurred_time']
                    if "timezone" in general_form.cleaned_data:
                        account = request.user.account
                        account.timezone = general_form.cleaned_data["timezone"]
                        account.save()
                        occurred_time = change_time_to_current_timezone(occurred_time)
                    game.end_time = occurred_time
                if "scenario" in general_form.changed_data:
                    game.scenario = general_form.cleaned_data['scenario']
                    # Updating scenario discoveries happens on attendance save.
                game.title = general_form.cleaned_data['title']
                game.save()
                for form in outcome_formset:
                    _update_or_add_attendance(request, form, game)
                game.refresh_from_db()
                game.recalculate_golden_ratio(original_game_ratio)
                if hasattr(game, "cell") and game.cell:
                    game.cell.update_safety_stats()
        else:
            raise ValueError("Invalid outcome formset in completed edit")
    else:
        raise ValueError("Invalid general info formset in completed edit")

def _update_or_add_attendance(request, form, game):
    player = get_object_or_404(User, id=form.cleaned_data['player_id'])
    is_confirmed = False
    if 'attending_character' in form.cleaned_data \
            and form.cleaned_data['attending_character']:
        if hasattr(form.cleaned_data['attending_character'], 'cell'):
            if not form.cleaned_data['attending_character'].cell == game.cell:
                is_confirmed = False
        else:
            is_confirmed = False
    else:
        is_confirmed = False
    if request.user.id == player.id:
        is_confirmed = True
    notes = None
    if "notes" in form.changed_data:
        notes = form.cleaned_data['notes']
    attending_character = None
    if 'attending_character' in form.cleaned_data \
            and not form.cleaned_data['attending_character'] is None:
        attending_character = form.cleaned_data['attending_character']
    if form.cleaned_data['attendance_id']:
        # Edit existing Attendance
        attendance = get_object_or_404(Game_Attendance, id=form.cleaned_data['attendance_id'])
        if notes:
            attendance.notes = notes
        attendance.save() # always resave the attendance because that's how we do scenario discoveries.
        if 'attending_character' in form.changed_data or 'outcome' in form.changed_data:
            attendance.change_outcome(new_outcome=form.cleaned_data['outcome'],
                                      is_confirmed=is_confirmed,
                                      attending_character=attending_character)
    else:
        # New Attendance
        attendance = Game_Attendance(
            relevant_game=game,
            notes=notes,
            outcome=form.cleaned_data['outcome'],
            is_confirmed=is_confirmed,
            attending_character = attending_character,
        )
        game_invite = Game_Invite(invited_player=player,
                                  relevant_game=game,
                                  as_ringer=False,)
        game_invite.save()
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        attendance.give_reward()

def _get_general_completed_form_for_edit(game, POST=None):
    GenInfoForm = make_archive_game_general_info_form(game.gm)
    return GenInfoForm(POST,
                       prefix="general",
                       initial={"gm_id": game.gm.id,
                                "scenario": game.scenario,
                                "title": game.title,
                                "occurred_time": game.end_time,
                                })


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


def get_context_for_choose_attending(cell, game=None):
    gm_form = get_gm_form(cell)
    outsider_form_set = get_outsider_formset()
    member_formset = get_member_formset(cell, game)
    return {
        'gm_form': gm_form,
        'member_formset': member_formset,
        'outsider_formset': outsider_form_set,
        'cell': cell,
        'game': game,
    }


def get_gm_form(cell, POST=None):
    WhoWasGm = make_who_was_gm_form(cell)
    return WhoWasGm(POST, prefix="gm")


def get_member_formset(cell, game=None, POST=None):
    cell_members = cell.cellmembership_set.all()
    MemberFormSet = formset_factory(CellMemberAttendedForm, extra=0)
    attended_players = set()
    if game:
        attended_players = {player.id for player in game.get_attended_players()}
    return MemberFormSet(POST,
                         prefix="member",
                         initial=[{'player_id': x.member_player.id,
                                   'username': x.member_player}
                                  for x in cell_members if x.member_player.id not in attended_players])


def get_outsider_formset(POST=None):
    OutsiderFormSet = formset_factory(OutsiderAttendedForm, extra=3)
    return OutsiderFormSet(POST, prefix="outsider")


def get_players_for_new_attendances(member_formset, outsider_formset):
    players = []
    for form in member_formset:
        if form.cleaned_data['attended']:
            players.append(form.cleaned_data['player_id'])
    for form in outsider_formset:
        if 'username' in form.cleaned_data:
            user = get_object_or_404(User, username=form.cleaned_data['username'])
            players.append(str(user.id))
    return players