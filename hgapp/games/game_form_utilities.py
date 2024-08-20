from datetime import datetime
import pytz

from django.forms import formset_factory
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.models import User

from .forms import make_archive_game_general_info_form, get_archival_outcome_form, CellMemberAttendedForm, OutsiderAttendedForm, \
    make_who_was_gm_form, ScenarioConditionCircumstanceForm, ScenarioLooseEndForm
from .models import Game, Game_Invite, Game_Attendance, GameEnded, ScenarioElement
from .games_constants import GAME_STATUS

from characters.models import LOOSE_END, StockWorldElement, StockElementCategory
from notifications.models import Notification, CONTRACT_NOTIF

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
    ArchivalOutcomeFormset = formset_factory(get_archival_outcome_form(game.id), extra=0)
    initial_existing = [{'player_id': attendance.get_player().id,
                         'attendance_id': attendance.id,
                         'invited_player': attendance.get_player(),
                         'attending_character': attendance.attending_character,
                         'outcome': attendance.outcome,
                         'MVP': attendance.is_mvp,
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
            if len([x for x in outcome_formset if x.cleaned_data["MVP"]]) > 1:
                raise ValueError("More than one MVP in completed edit")
            with transaction.atomic():
                Game.objects.select_for_update().get(pk=game.pk)
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
                if "cell" in general_form.changed_data:
                    game.cell = general_form.cleaned_data['cell']
                game.save()
                for form in outcome_formset:
                    _update_or_add_attendance(request, form, game)
                game.refresh_from_db()
                game.recalculate_gm_reward()
                game.update_profile_stats()
                game.unlock_stock_scenarios()
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
        if 'attending_character' in form.changed_data or 'outcome' in form.changed_data or 'MVP' in form.changed_data:
            attendance.change_outcome(new_outcome=form.cleaned_data['outcome'],
                                      is_confirmed=is_confirmed,
                                      attending_character=attending_character,
                                      is_mvp=form.cleaned_data["MVP"])
    else:
        # New Attendance
        attendance = Game_Attendance(
            relevant_game=game,
            notes=notes,
            outcome=form.cleaned_data['outcome'],
            is_confirmed=is_confirmed,
            attending_character = attending_character,
            is_mvp=form.cleaned_data["MVP"],
        )
        game_invite = Game_Invite(invited_player=player,
                                  relevant_game=game,
                                  as_ringer=False,)
        game_invite.save()
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        attendance.give_reward()
    if not is_confirmed:
        Notification.objects.create(
            user=player,
            headline="{} says you attended a Contract".format(game.gm.username),
            content="Click here to confirm or deny your attendance",
            url=reverse('games:games_view_game', args=(game.id,)),
            notif_type=CONTRACT_NOTIF)


def _get_general_completed_form_for_edit(game, POST=None):
    GenInfoForm = make_archive_game_general_info_form(game.gm)
    return GenInfoForm(POST,
                       prefix="general",
                       initial={"gm_id": game.gm.id,
                                "scenario": game.scenario,
                                "occurred_time": game.end_time,
                                "cell": game.cell,
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
            title="",
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
        cell.find_world_date = occurred_time
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
                    character = form.cleaned_data['attending_character']
                    attendance.attending_character = character
                    character.highlight_crafting = True
                    character.save()
                    if not form.cleaned_data['attending_character'].cell == cell:
                        attendance.is_confirmed = False
                    elif game.creator.id != player.id:
                        character.progress_loose_ends(occurred_time)
                else:
                    attendance.is_confirmed = False
            else:
                game_invite.as_ringer = True
                attendance.is_confirmed = False
            if game.creator.id == player.id:
                attendance.is_confirmed = True
                attendance.attending_character.progress_loose_ends(occurred_time)
            attendance.is_mvp = form.cleaned_data["MVP"]
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            if not attendance.is_confirmed:
                Notification.objects.create(
                    user=player,
                    headline="{} says you attended a Contract".format(game.gm.username),
                    content="Click here to confirm or deny your attendance",
                    url=reverse('games:games_view_game', args=(game.id,)),
                    notif_type=CONTRACT_NOTIF)
        game.give_rewards()
        game.update_profile_stats()
        game.unlock_stock_scenarios()
    GameEnded.send_robust(sender=None, game=game, request=request)


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
    cell_members = cell.get_unbanned_members()
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


def get_element_formset_empty(POST, element_type):
    if element_type == LOOSE_END:
        return formset_factory(ScenarioLooseEndForm, extra=0)(POST, prefix="loose-end", initial=[])
    else:
        return formset_factory(ScenarioConditionCircumstanceForm, extra=0)(POST, prefix=element_type, initial=[])


def get_element_formset(scenario, POST, element_type):
    elements = scenario.get_latest_of_all_elements_of_type(element_type)
    if element_type == LOOSE_END:
        initial = [{
            "designation": x.designation,
            "name": x.relevant_element.name,
            "threat": x.relevant_element.system,
            "details": x.relevant_element.description,
            "cutoff": x.relevant_element.cutoff,
            "how_to_tie_up": x.relevant_element.how_to_tie_up,
            "threat_level": x.relevant_element.threat_level,
        } for x in elements if not x.is_deleted]
        return formset_factory(ScenarioLooseEndForm, extra=0)(POST, prefix="loose-end", initial=initial)
    else:
        initial = [{
            "designation": x.designation,
            "type": x.type,
            "name": x.relevant_element.name,
            "system": x.relevant_element.system,
            "description": x.relevant_element.description,
        } for x in elements if not x.is_deleted]
        return formset_factory(ScenarioConditionCircumstanceForm, extra=0)(POST, prefix=element_type, initial=initial)


def save_new_elements_from_formsets(request, scenario, formset, element_type):
    scenario_category = StockElementCategory.objects.filter(name="Scenario").first()
    if not scenario_category:
        scenario_category = StockElementCategory.objects.create(name="Scenario")
    is_loose_end = element_type == LOOSE_END
    for form in formset:
        if "designation" in form.cleaned_data and len(form.cleaned_data["designation"]) > 0:
            # edit
            if not form.changed_data:
                continue # nothing changed
            save_element_from_form(form, is_loose_end, request, scenario, form.cleaned_data["designation"], element_type, scenario_category)
        else:
            # new
            if "is_deleted" in form.cleaned_data and form.cleaned_data["is_deleted"]:
                # don't need to persist anything for new + deleted forms.
                continue
            new_designation = "{} {}".format(
                element_type,
                scenario.scenarioelement_set.filter(type=element_type).distinct("designation").count() + 1)
            save_element_from_form(form, is_loose_end, request, scenario, new_designation, element_type, scenario_category)


def save_element_from_form(form, is_loose_end, request, scenario, designation, element_type, scenario_category):
    description = form.cleaned_data["details"] if is_loose_end else form.cleaned_data["description"]
    system = form.cleaned_data["threat"] if is_loose_end else form.cleaned_data["system"]
    new_element = StockWorldElement(
        name=form.cleaned_data["name"],
        description=description,
        system=system,
        type=element_type,
        is_user_created=True,
        category=scenario_category
    )
    if is_loose_end:
        new_element.cutoff = form.cleaned_data["cutoff"]
        new_element.how_to_tie_up = form.cleaned_data["how_to_tie_up"]
        new_element.threat_level = form.cleaned_data["threat_level"]
    new_element.save()
    new_scenario_element = ScenarioElement(creator=request.user,
                                           designation=designation,
                                           relevant_element=new_element,
                                           relevant_scenario=scenario,
                                           type=element_type,
                                           is_deleted=form.cleaned_data["is_deleted"])
    new_scenario_element.save()


