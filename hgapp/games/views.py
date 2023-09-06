from django.contrib.auth.models import User
from heapq import merge
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms import formset_factory
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View
from django.conf import settings

import requests
import datetime
import logging
from collections import defaultdict

logger = logging.getLogger("app." + __name__)

from games.forms import CreateScenarioForm, CellMemberAttendedForm, make_game_form, make_allocate_improvement_form, \
    CustomInviteForm, make_accept_invite_form, ValidateAttendanceForm, DeclareOutcomeForm, GameFeedbackForm, \
    OutsiderAttendedForm, make_who_was_gm_form,make_archive_game_general_info_form, get_archival_outcome_form, \
    RsvpAttendanceForm, make_edit_move_form, ScenarioWriteupForm, RevertToEditForm, make_grant_stock_element_form, \
    make_grant_element_form, SpoilScenarioForm, ScenarioApprovalForm
from .game_form_utilities import get_context_for_create_finished_game, change_time_to_current_timezone, convert_to_localtime, \
    create_archival_game, get_context_for_completed_edit, handle_edit_completed_game, get_context_for_choose_attending, \
    get_gm_form, get_outsider_formset, get_member_formset, get_players_for_new_attendances, get_element_formset, \
    save_new_elements_from_formsets, get_element_formset_empty
from .games_constants import GAME_STATUS, EXP_V1_V2_GAME_ID, get_completed_game_excludes_query

from cells.forms import EditWorldEventForm
from cells.models import WorldEvent

from games.models import Scenario, Game, DISCOVERY_REASON, Game_Invite, Game_Attendance, Reward, REQUIRED_HIGH_ROLLER_STATUS, \
    Move, GameChangeStartTime, GameEnded, ScenarioWriteup, MISSION, OVERVIEW, BACKSTORY, INTRODUCTION, AFTERMATH, \
    ScenarioElement, Scenario_Discovery, ScenarioApproval, WAITING, WITHDRAWN, REJECTED, EXCHANGE_SUBMISSION_VALUE

from profiles.models import Profile

from characters.models import Character, LOOSE_END, CONDITION, TROPHY, CIRCUMSTANCE, StockWorldElement

from characters.forms import get_default_world_element_choice_form

from hgapp.utilities import get_queryset_size, get_object_or_none

from cells.models import Cell

from notifications.models import Notification, SCENARIO_NOTIF, WORLD_NOTIF, CONTRACT_NOTIF

@login_required
def enter_game(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to enter a Game")
    if request.user.profile.get_confirmed_email() is None:
        messages.add_message(request, messages.WARNING,
                             mark_safe("<h4 class=\"text-center\" style=\"margin-bottom:5px;\">You must validate your email address to schedule a Contract</h4>"))
        return HttpResponseRedirect(reverse('account_resend_confirmation'))
    cells = [cell for cell in request.user.cell_set.filter(cellmembership__is_banned=False).all() if cell.player_can_manage_games(request.user)]
    context = {
        'cells' : cells,
    }
    return render(request, 'games/enter_game.html', context)


def view_other_scenarios(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.user != game.gm:
        raise PermissionDenied("Cannot view other Scenarios for a Contract you aren't the GM for")
    my_scenario_discoveries = Scenario_Discovery.objects\
        .filter(discovering_player=request.user)\
        .select_related("relevant_scenario")\
        .order_by("relevant_scenario__title")
    their_scenario_ids = set()
    for invite in game.get_accepted_invites():
        their_scenario_ids.update(Scenario_Discovery.objects
                                  .filter(discovering_player=invite.invited_player, is_spoiled=True)
                                  .values_list("relevant_scenario__pk", flat=True))
    runnable_scenarios = [x.relevant_scenario for x in my_scenario_discoveries if x.relevant_scenario.pk not in their_scenario_ids]
    runnable_scenarios_by_status = defaultdict(list)
    for scenario in runnable_scenarios:
        runnable_scenarios_by_status[scenario.get_suggested_status_display()].append(scenario)
    context = {
        "runnable_scenarios_by_status": dict(runnable_scenarios_by_status),
    }
    return render(request, 'games/view_game_pages/runnable_scenarios_content.html', context)


def activity(request):
    num_total_games = Game.objects.count()
    num_finished_games = Game.objects.exclude(get_completed_game_excludes_query()).count()
    num_players = Profile.objects.count()
    num_contractors = Character.objects.count()
    num_contractors_played = Character.objects.filter(num_games__gte=1).count()
    now = datetime.datetime.now()
    two_hours_ago = now - datetime.timedelta(hours=2)
    games_query = Game.objects.filter(
        status=GAME_STATUS[0][0],
        scheduled_start_time__gte=two_hours_ago)
    upcoming_games = games_query.order_by('-scheduled_start_time').all()
    past_games_query = Game.objects.filter(
        scheduled_start_time__lte=two_hours_ago)
    past_games = past_games_query.order_by('-scheduled_start_time','-actual_start_time').prefetch_related('gm', 'cell', 'scenario').all()
    num_scenarios_with_valid_writeups = Scenario.objects.filter(num_words__gte=1000).count()
    context = {
        "num_total_games": num_total_games,
        "num_finished_games": num_finished_games,
        "num_players": num_players,
        "num_contractors": num_contractors,
        "num_contractors_played": num_contractors_played,
        "num_scenarios_with_valid_writeups": num_scenarios_with_valid_writeups,
        "upcoming_games": upcoming_games,
        "past_games": past_games,
    }
    return render(request, 'games/activity.html', context)


@login_required
def create_scenario(request):
    if not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    POST = request.POST if request.method == "POST" else None;
    condition_formset = get_element_formset_empty(POST, CONDITION)
    circumstance_formset = get_element_formset_empty(POST, CIRCUMSTANCE)
    loose_end_formset = get_element_formset_empty(POST, LOOSE_END)
    trophy_formset = get_element_formset_empty(POST, TROPHY)
    if request.method == 'POST':
        scenario_form = CreateScenarioForm(request.POST)
        writeup_form = ScenarioWriteupForm(request.POST)
        if scenario_form.is_valid() and writeup_form.is_valid() \
                and condition_formset.is_valid() \
                and circumstance_formset.is_valid() \
                and loose_end_formset.is_valid() \
                and trophy_formset.is_valid():
            scenario = Scenario(
                title = scenario_form.cleaned_data['title'],
                creator = request.user,
                description = "legacy",
                objective=scenario_form.cleaned_data["objective"],
                summary=scenario_form.cleaned_data['summary'],
                max_players=scenario_form.cleaned_data['max_players'],
                min_players=scenario_form.cleaned_data['min_players'],
                suggested_status=scenario_form.cleaned_data['suggested_character_status'],
                is_highlander=scenario_form.cleaned_data['is_highlander'],
                requires_ringer=scenario_form.cleaned_data['requires_ringer'],
                is_rivalry=scenario_form.cleaned_data['is_rivalry']
            )
            if request.user.is_superuser:
                scenario.tags.set(scenario_form.cleaned_data["tags"])
            new_writeups = get_writeups_from_form(request, scenario,writeup_form)
            with transaction.atomic():
                scenario.save()
                for writeup in new_writeups:
                    writeup.save()
                scenario.update_word_count()
                scenario.save()
                save_new_elements_from_formsets(request, scenario, condition_formset, CONDITION)
                save_new_elements_from_formsets(request, scenario, circumstance_formset, CIRCUMSTANCE)
                save_new_elements_from_formsets(request, scenario, loose_end_formset, LOOSE_END)
                save_new_elements_from_formsets(request, scenario, trophy_formset, TROPHY)
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            print(scenario_form.errors)
            return None
    else:
        scenario_form = CreateScenarioForm()
        writeup_form = ScenarioWriteupForm()
        context = {
            'scenario_form': scenario_form,
            'writeup_form': writeup_form,
            'condition_formset': condition_formset,
            'circumstance_formset': circumstance_formset,
            'trophy_formset': trophy_formset,
            'loose_end_formset': loose_end_formset,
        }
        return render(request, 'games/scenarios/edit_scenario.html', context)


@login_required
def edit_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    if request.user.profile.get_confirmed_email() is None:
        messages.add_message(request, messages.WARNING,
                             mark_safe("<h4 class=\"text-center\" style=\"margin-bottom:5px;\">You must validate your email address to edit Scenarios</h4>"))
        return HttpResponseRedirect(reverse('account_resend_confirmation'))
    aftermath_spoiled = scenario.is_player_aftermath_spoiled(request.user)
    if not aftermath_spoiled:
        return HttpResponseRedirect(reverse('games:spoil_scenario_aftermath', args=(scenario.id, "edit")))
    can_edit_scenario = request.user.has_perm('edit_scenario', scenario)
    overview = scenario.get_latest_of_section(OVERVIEW)
    backstory = scenario.get_latest_of_section(BACKSTORY)
    introduction = scenario.get_latest_of_section(INTRODUCTION)
    mission = scenario.get_latest_of_section(MISSION)
    aftermath = scenario.get_latest_of_section(AFTERMATH)
    writeup_form_initial = {"overview": overview.content if overview else None,
                            "backstory": backstory.content if backstory else None,
                            "introduction": introduction.content if introduction else None,
                            "mission": mission.content if mission else None,
                            "aftermath": aftermath.content if aftermath else None, }
    POST = request.POST if request.method == "POST" else None;
    condition_formset = get_element_formset(scenario, POST, CONDITION)
    circumstance_formset = get_element_formset(scenario, POST, CIRCUMSTANCE)
    loose_end_formset = get_element_formset(scenario, POST, LOOSE_END)
    trophy_formset = get_element_formset(scenario, POST, TROPHY)
    if request.method == 'POST':
        scenario_form = None
        if can_edit_scenario:
            scenario_form = CreateScenarioForm(request.POST)
        writeup_form = ScenarioWriteupForm(request.POST, initial=writeup_form_initial)
        if (not scenario_form or (scenario_form and scenario_form.is_valid())) \
                and writeup_form.is_valid() \
                and condition_formset.is_valid() \
                and circumstance_formset.is_valid() \
                and loose_end_formset.is_valid() \
                and trophy_formset.is_valid():
            if can_edit_scenario:
                scenario.title = scenario_form.cleaned_data['title']
                scenario.summary = scenario_form.cleaned_data['summary']
                scenario.objective = scenario_form.cleaned_data['objective']
                scenario.max_players = scenario_form.cleaned_data['max_players']
                scenario.min_players = scenario_form.cleaned_data['min_players']
                scenario.suggested_status = scenario_form.cleaned_data['suggested_character_status']
                scenario.is_highlander = scenario_form.cleaned_data['is_highlander']
                scenario.is_rivalry = scenario_form.cleaned_data['is_rivalry']
                scenario.is_wiki_editable = scenario_form.cleaned_data['is_wiki_editable']
                scenario.requires_ringer = scenario_form.cleaned_data['requires_ringer']
                if request.user.is_superuser:
                    scenario.tags.set(scenario_form.cleaned_data["tags"])
            new_writeups = get_writeups_from_form(request, scenario, writeup_form)
            with transaction.atomic():
                for writeup in new_writeups:
                    writeup.save()
                scenario.update_word_count()
                scenario.save()
                save_new_elements_from_formsets(request, scenario, condition_formset, CONDITION)
                save_new_elements_from_formsets(request, scenario, circumstance_formset, CIRCUMSTANCE)
                save_new_elements_from_formsets(request, scenario, loose_end_formset, LOOSE_END)
                save_new_elements_from_formsets(request, scenario, trophy_formset, TROPHY)
                if request.user != scenario.creator:
                    Notification.objects.create(user=scenario.creator,
                                                headline="New edit on your Scenario",
                                                content=scenario.title,
                                                url=reverse('games:scenario_history', args=(scenario.id,)),
                                                notif_type=SCENARIO_NOTIF)
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            raise ValueError("Invalid form " + str(writeup_form.errors) + " scenario: " + str(scenario_form.errors))
    else:
        scenario_form = None
        if can_edit_scenario:
            scenario_form = CreateScenarioForm(initial={
                'title': scenario.title,
                'summary': scenario.summary,
                'objective': scenario.objective,
                'max_players': scenario.max_players,
                'min_players': scenario.min_players,
                'suggested_character_status': scenario.suggested_status,
                'is_highlander': scenario.is_highlander,
                'is_rivalry': scenario.is_rivalry,
                'is_wiki_editable': scenario.is_wiki_editable,
                'requires_ringer': scenario.requires_ringer,
                'tags': scenario.tags.all(),
            })
        writeup_form = ScenarioWriteupForm(initial=writeup_form_initial)
        context = {
            'scenario': scenario,
            'scenario_form': scenario_form,
            'writeup_form': writeup_form,
            'condition_formset': condition_formset,
            'circumstance_formset': circumstance_formset,
            'trophy_formset': trophy_formset,
            'loose_end_formset': loose_end_formset,
        }
        return render(request, 'games/scenarios/edit_scenario.html', context)


@login_required
def submit_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    if request.user.profile.get_confirmed_email() is None:
        messages.add_message(request, messages.WARNING,
                             mark_safe("<h4 class=\"text-center\" style=\"margin-bottom:5px;\">You must validate your email address to submit Scenarios</h4>"))
        return HttpResponseRedirect(reverse('account_resend_confirmation'))
    if scenario.creator != request.user:
        raise PermissionDenied("Only a Scenario's creator can submit it to the exchange.")
    if request.method == 'POST':
        if len(scenario.get_steps_to_receive_improvement) > 0:
            raise ValueError("Scenario does not meet requirements for exchange")
        form = RsvpAttendanceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                open_approval = ScenarioApproval.objects.filter(relevant_scenario=scenario, status=WAITING).first()
                if open_approval:
                    return HttpResponseRedirect(reverse('games:games_scenario_submit', args=(scenario.id,)))
                else:
                    ScenarioApproval.objects.create(relevant_scenario=scenario)
        else:
            raise ValueError("Invalid Scenario Exchange submission form")
        return HttpResponseRedirect(reverse('games:games_scenario_submit', args=(scenario.id,)))
    form = RsvpAttendanceForm()
    latest_approval = ScenarioApproval.objects.filter(relevant_scenario=scenario).order_by("-created_date").first()
    approvals = ScenarioApproval.objects.filter(relevant_scenario=scenario).order_by("-created_date")
    context = {
        "scenario": scenario,
        "latest_approval": latest_approval,
        "approvals": approvals,
        "form": form,
        "submission_value": EXCHANGE_SUBMISSION_VALUE,
    }
    return render(request, 'games/scenarios/submit_scenario.html', context)

@login_required
def retract_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    if scenario.creator != request.user:
        raise PermissionDenied("Only a Scenario's creator can submit it to the exchange.")
    if request.method == 'POST':
        form = RsvpAttendanceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                open_approval = ScenarioApproval.objects.filter(relevant_scenario=scenario, status=WAITING).first()
                if open_approval:
                    open_approval.status = WITHDRAWN
                    open_approval.closed_date = timezone.now()
                    open_approval.approver = request.user
                    open_approval.save()
                    return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            raise ValueError("Invalid Scenario Exchange submission form")
        return HttpResponseRedirect(reverse('games:games_scenario_submit', args=(scenario.id,)))
    HttpResponseRedirect(reverse('games:games_scenario_submit', args=(scenario.id,)))


@login_required
def approve_scenarios(request):
    if not (request.user.profile.exchange_approver or request.user.is_superuser):
        raise PermissionDenied("You must be an exchange approver to approve Scenarios")
    context = {
        "outstanding_approvals": ScenarioApproval.objects.filter(status=WAITING).order_by("created_date"),
        "closed_approvals": ScenarioApproval.objects.filter(closed_date__isnull=False).order_by("-closed_date")[:20],
        "form": ScenarioApprovalForm(),
    }
    return render(request, 'games/scenarios/approve_scenarios.html', context)


@login_required
def approve_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not (request.user.profile.exchange_approver or request.user.is_superuser):
        raise PermissionDenied("You must be an exchange approver to approve Scenarios")
    if request.method == 'POST':
        form = ScenarioApprovalForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                open_approval = ScenarioApproval.objects.filter(relevant_scenario=scenario, status=WAITING).first()
                if open_approval:
                    if "is_approved" in form.cleaned_data and form.cleaned_data["is_approved"]:
                        open_approval.approve(request.user)
                    else:
                        open_approval.status = REJECTED
                        open_approval.closed_date = timezone.now()
                        open_approval.feedback = form.cleaned_data["feedback"]
                        open_approval.approver = request.user
                        open_approval.save()
                        Notification.objects.create(
                            user=open_approval.relevant_scenario.creator,
                            headline="Your Scenario has been rejected",
                            content="{} left feedback on {}.".format(request.user.username,
                                                                     open_approval.relevant_scenario.title),
                            url=reverse('games:games_scenario_submit', args=(open_approval.relevant_scenario_id,)),
                            notif_type=SCENARIO_NOTIF)
                    return HttpResponseRedirect(reverse('games:games_scenario_approve'))
        else:
            raise ValueError("Invalid Scenario Exchange submission form")
    return HttpResponseRedirect(reverse('games:games_scenario_approve'))


def get_writeups_from_form(request, scenario, writeup_form):
    writeup_time = timezone.now()
    new_writeups = []
    if "overview" in writeup_form.changed_data:
        new_writeups.append(ScenarioWriteup(created_date=writeup_time,
                                            writer=request.user,
                                            relevant_scenario=scenario,
                                            section=OVERVIEW,
                                            content=writeup_form.cleaned_data["overview"]))
    if "backstory" in writeup_form.changed_data:
        new_writeups.append(ScenarioWriteup(created_date=writeup_time,
                                            writer=request.user,
                                            relevant_scenario=scenario,
                                            section=BACKSTORY,
                                            content=writeup_form.cleaned_data["backstory"]))
    if "introduction" in writeup_form.changed_data:
        new_writeups.append(ScenarioWriteup(created_date=writeup_time,
                                            writer=request.user,
                                            relevant_scenario=scenario,
                                            section=INTRODUCTION,
                                            content=writeup_form.cleaned_data["introduction"]))
    if "mission" in writeup_form.changed_data:
        new_writeups.append(ScenarioWriteup(created_date=writeup_time,
                                            writer=request.user,
                                            relevant_scenario=scenario,
                                            section=MISSION,
                                            content=writeup_form.cleaned_data["mission"]))
    if "aftermath" in writeup_form.changed_data:
        new_writeups.append(ScenarioWriteup(created_date=writeup_time,
                                            writer=request.user,
                                            relevant_scenario=scenario,
                                            section=AFTERMATH,
                                            content=writeup_form.cleaned_data["aftermath"]))
    return new_writeups

def view_scenario(request, scenario_id, game_id=None):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not scenario.is_public() and not request.user.is_authenticated:
        raise PermissionDenied("You don't have permission to view this scenario")
    if not scenario.is_public() and not (scenario.player_discovered(request.user) or request.user.is_superuser):
        raise PermissionDenied("You don't have permission to view this scenario")
    if request.user.is_authenticated and scenario.is_spoilable_for_player(request.user):
        return HttpResponseRedirect(reverse('games:games_spoil_scenario', args=(scenario.id,)))

    if request.method == 'POST':
        form = GameFeedbackForm(request.POST)
        if form.is_valid() and game_id:
            game = get_object_or_none(Game, id=game_id)
            if game and game.gm.id == request.user.id and str(game.scenario.id) == scenario_id:
                with transaction.atomic():
                    game = get_object_or_404(Game, id=game_id)
                    if game.gm.id == request.user.id:
                        game.scenario_notes = form.cleaned_data['scenario_notes']
                        game.save()
            else:
                raise ValueError("Invalid Game for feedback")
        return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
    else:
        if request.user.is_authenticated and scenario.player_has_gmed(request.user):
            grant_element_form = make_grant_stock_element_form(scenario, request.user)
        else:
            grant_element_form = None
        viewer_can_edit = False
        if request.user.is_authenticated:
            viewer_can_edit = scenario.player_can_edit_writeup(request.user)
        games_completed = scenario.finished_games().order_by("-end_time")
        game_feedback_form = GameFeedbackForm()
        is_public = scenario.is_public()
        sections = scenario.get_latest_of_all_writeup_sections()
        elements = defaultdict(list)
        for element in scenario.get_latest_of_all_elements():
            if not element.is_deleted:
                elements[element.get_type_plural()].append(element)
        aftermath_spoiled = scenario.is_player_aftermath_spoiled(request.user)
        if aftermath_spoiled:
            players_gmed_for = scenario.get_players_gmed_for(request.user).values_list("pk", flat=True)
            query = scenario.scenario_discovery_set.filter(
                reason=DISCOVERY_REASON[0][0],
                is_aftermath_spoiled=True,
                discovering_player__id__in=players_gmed_for)
            players_aftermath_spoiled = [x.discovering_player.username for x in query]
        else:
            players_aftermath_spoiled = []
        context = {
            'aftermath_spoiled': aftermath_spoiled,
            'scenario': scenario,
            'is_public': is_public,
            'viewer_can_edit': viewer_can_edit,
            'games_completed': games_completed,
            'game_feedback_form': game_feedback_form,
            'writeup_sections': sections,
            'last_edit': scenario.get_last_edit(),
            "elements": dict(elements),
            "grant_element_form": grant_element_form,
            'players_aftermath_spoiled': players_aftermath_spoiled,
        }
        return render(request, 'games/scenarios/view_scenario.html', context)


def view_scenario_history(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not scenario.is_public() and not request.user.is_authenticated:
        raise PermissionDenied("You don't have permission to view this scenario")
    if not scenario.is_public() and not scenario.player_discovered(request.user):
        raise PermissionDenied("You don't have permission to view this scenario")
    if request.method == 'POST':
        if not scenario.player_can_edit_writeup(request.user):
            raise PermissionDenied("You don't have permission to edit this scenario")
        form = RevertToEditForm(request.POST)
        if form.is_valid():
            writeup = get_object_or_404(ScenarioWriteup, id=form.cleaned_data["writeup_id"])
            if writeup.relevant_scenario != scenario:
                raise ValueError("Writeup is not for this scenario.")
            if writeup.is_most_recent_for_section():
                raise ValueError("Writeup is most recent for the given section.")
            new_writeup = ScenarioWriteup(relevant_scenario=scenario,
                                          writer=request.user,
                                          content=writeup.content,
                                          section=writeup.section)
            with transaction.atomic():
                new_writeup.save()
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            raise ValueError("Invalid writeup revert form.")
    else:
        edits = ScenarioWriteup.objects.filter(relevant_scenario=scenario).order_by("-created_date").all()
        element_edits = ScenarioElement.objects.filter(relevant_scenario=scenario).order_by("-created_date").all()
        aftermath_spoiled = scenario.is_player_aftermath_spoiled(request.user)
        writeup_edit_blobs = [x.to_blob(request, aftermath_spoiled) for x in edits]
        element_edit_blobs = [x.to_blob(request, aftermath_spoiled) for x in element_edits]
        edit_blobs = merge(writeup_edit_blobs, element_edit_blobs, key=lambda x: x["created_date"], reverse=True)
        form = RevertToEditForm()
        viewer_can_edit = scenario.player_can_edit_writeup(request.user)
        context = {
            "scenario": scenario,
            "form": form,
            "page_data": {
                "edits": list(edit_blobs),
                "can_edit": viewer_can_edit,
            },
        }
        return render(request, 'games/scenarios/scenario_edit_history.html', context)


@login_required
def spoil_aftermath(request, scenario_id, reason):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not scenario.player_is_spoiled(request.user):
        raise PermissionDenied("You cannot spoil this Scenario's aftermath if you can't yet view the Scenario.")
    if request.method == 'POST':
        form = SpoilScenarioForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                scenario.spoil_aftermath(request.user)
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            raise ValueError("Invalid aftermath spoil form")
    else:
        context = {
            "scenario": scenario,
            "spoil_form": SpoilScenarioForm(),
            "for_edit": reason == "edit",
            "dest": reason,
        }
        return render(request, 'games/scenarios/spoil_aftermath.html', context)



@login_required
def grant_element(request, element_id):
    if request.is_ajax and request.method == "POST":
        element = get_object_or_404(ScenarioElement, id=element_id)
        scenario = element.relevant_scenario
        if not scenario.player_is_spoiled(request.user):
            return JsonResponse({"error": "forbidden"}, status=403)

        grant_element_form = make_grant_stock_element_form(scenario, request.user)(request.POST)
        if grant_element_form.is_valid():
            with transaction.atomic():
                character = grant_element_form.cleaned_data["contractor"]
                if not character.player_can_edit(request.user):
                    raise PermissionDenied("do not have permissions to edit character")
                game = character.get_scenario_attendance(scenario)
                if game and game.relevant_game.cell:
                    cell = game.relevant_game.cell
                else:
                    cell=None
                element.relevant_element.grant_to_character_no_trauma(character, request.user, cell)
            return JsonResponse({"name": character.name}, status=200)
    return JsonResponse({"error": ""}, status=400)

@login_required
def view_scenario_gallery(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to view your Scenario Gallery")
    owned_scenarios = request.user.scenario_creator.order_by("-times_run", "-num_words").all()
    discovered_scenarios = request.user.scenario_discovery_set.exclude(reason=DISCOVERY_REASON[1][0]).exclude(is_spoiled=False).order_by("-relevant_scenario__times_run", "-relevant_scenario__num_words").all()
    unlocked_scenarios = request.user.scenario_discovery_set.exclude(is_spoiled=True).all()
    not_cell_leader = request.user.cell_set.filter(creator=request.user).count() == 0
    scenarios_to_unlock = [scenario for scenario in Scenario.objects.filter(tags__isnull=False).all() if not scenario.player_discovered(request.user)]
    context = {
        'owned_scenarios': owned_scenarios,
        'scenario_discoveries': discovered_scenarios,
        'unlocked_discoveries': unlocked_scenarios,
        'scenarios_to_unlock': scenarios_to_unlock,
        'not_cell_leader': not_cell_leader,
    }
    return render(request, 'games/view_scenario_gallery.html', context)


@login_required
def create_game(request, cell_id=None):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to schedule a Contract")
    if request.user.profile.get_confirmed_email() is None:
        messages.add_message(request, messages.WARNING,
                             mark_safe("<h4 class=\"text-center\" style=\"margin-bottom:5px;\">You must validate your email address to schedule a Contract</h4>"))
        return HttpResponseRedirect(reverse('account_resend_confirmation'))
    cell = None
    if cell_id:
        cell = get_object_or_404(Cell, id=cell_id)
    GameForm = make_game_form(user=request.user)
    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            start_time = form.cleaned_data['scheduled_start_time']
            if "timezone" in form.cleaned_data:
                account = request.user.account
                account.timezone = form.cleaned_data["timezone"]
                account.save()
                start_time = change_time_to_current_timezone(start_time)
            title = form.cleaned_data['title'] if "title" in form.cleaned_data and form.cleaned_data['title'] else "untitled"
            form_cell = form.cleaned_data['cell']
            if not form_cell.get_player_membership(request.user):
                raise PermissionDenied("You are not a member of this Playgroup.")
            if not (form_cell.player_can_manage_games(request.user) or form_cell.player_can_run_games(request.user)):
                raise PermissionDenied("You do not have permission to run Contracts in this Playgroup")
            game = Game(
                title = title,
                creator = request.user,
                gm = request.user,
                required_character_status = form.cleaned_data['required_character_status'],
                hook = form.cleaned_data['hook'],
                created_date = timezone.now(),
                scheduled_start_time = start_time,
                status = GAME_STATUS[0][0],
                cell = form_cell,
                invitation_mode=form.cleaned_data['invitation_mode'],
                list_in_lfg=form.cleaned_data['list_in_lfg'],
                allow_ringers=form.cleaned_data['allow_ringers'],
                max_rsvp=form.cleaned_data['max_rsvp'],
                gametime_url=form.cleaned_data['gametime_url'],
                )
            if 'only_over_18' in form.cleaned_data:
                game.is_nsfw = form.cleaned_data['only_over_18']
            if form.cleaned_data['scenario']:
                game.scenario = form.cleaned_data['scenario']
                game.title = game.scenario.title
            with transaction.atomic():
                game.save()
                game.mediums.set(form.cleaned_data['mediums'])
                if form.cleaned_data['invite_all_members']:
                    for member in game.cell.get_unbanned_members().exclude(member_player = game.gm):
                        game_invite = Game_Invite(invited_player=member.member_player,
                                                  relevant_game=game,
                                                  invite_text=game.hook,
                                                  as_ringer=False)
                        if member.member_player.has_perm("view_scenario", game.scenario):
                            game_invite.as_ringer = True
                        game_invite.save()
                        game_invite.notify_invitee(request, game)
            messages.add_message(request, messages.SUCCESS, mark_safe("Your Contract has been successfully scheduled."))
            post_game_webhook(game, request)
            return HttpResponseRedirect(reverse('games:games_invite_players', args=(game.id,)))
        else:
            logger.error('Error: invalid GameForm. Errors: %s', str(form.errors))
            raise ValueError("Invalid game form")
    else:
        # Build a game form.
        form = GameForm(initial={"cell": cell})
        scenarios_by_cells = get_scenarios_by_cells(request)
        context = {
            'form': form,
            'scenarios_by_cells': scenarios_by_cells,
        }
        return render(request, 'games/edit_game.html', context)


def post_game_webhook(game, request, is_changed_start=False):
    cell_webhooks = game.cell.webhook_cell.filter(send_for_contracts=True).all()
    if game.list_in_lfg or cell_webhooks:
        content = game.get_webhook_post(request, is_changed_start)
        if game.list_in_lfg:
            lfg_content = "{} {}".format("<@&921821283551940638>", content)
            requests.post(settings.LFG_WEBHOOK_URL, json={'content': lfg_content, })
            if game.required_character_status in [REQUIRED_HIGH_ROLLER_STATUS[1][0], REQUIRED_HIGH_ROLLER_STATUS[2][0]] \
                and game.gm.pk in [23, 11, 156, 116, 169, 55, 203, 142, 552, 529, 414, 339]:
                # LFG newbie game posted by approved GM.
                content_newbie = "{} {}".format("<@&921870632138965063>", content)
                requests.post(settings.NEWBIE_WEBHOOK_URL, json={'content': content_newbie, })
        for webhook in cell_webhooks:
            webhook.post(content)


def get_scenarios_by_cells(request):
    user_cells = request.user.cell_set.all()
    scenarios_by_cells = defaultdict(set)
    for cell in user_cells:
        scenarios_by_cells[cell.id] = list(set(
            Game.objects.filter(cell=cell, scenario__isnull=False).select_related('scenario').values(
                'scenario__id').distinct().values_list('id', flat=True)))
    return scenarios_by_cells


@login_required
def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.user.is_anonymous or not game.player_can_edit(request.user):
        raise PermissionDenied("You don't have permission to edit this Game event.")
    if not game.is_scheduled():
        raise PermissionDenied("You cannot edit a Game event once it has started.")
    initial_data = {
     'hook': game.hook,
     'scenario': game.scenario,
     'required_character_status': game.required_character_status,
     'start_time': convert_to_localtime(game.scheduled_start_time),
     'cell': game.cell,
     'only_over_18': game.is_nsfw,
     'invitation_mode': game.invitation_mode,
     'list_in_lfg': game.list_in_lfg,
     'allow_ringers': game.allow_ringers,
     'max_rsvp': game.max_rsvp,
     'gametime_url': game.gametime_url,
     'invite_all_members': game.invite_all_members,
     'mediums': game.mediums.all(),
    }
    GameForm = make_game_form(user=request.user)
    if request.method == 'POST':
        form = GameForm(request.POST, initial=initial_data)
        if form.is_valid():
            title = form.cleaned_data['title'] if "title" in form.cleaned_data and form.cleaned_data['title'] else "untitled"
            game.title = title
            game.hook=form.cleaned_data['hook']
            start_time = form.cleaned_data['scheduled_start_time']
            if "timezone" in form.cleaned_data:
                account = request.user.account
                account.timezone = form.cleaned_data["timezone"]
                account.save()
                start_time = change_time_to_current_timezone(start_time)
            changed_start = start_time != game.scheduled_start_time
            game.scheduled_start_time = start_time
            game.required_character_status = form.cleaned_data['required_character_status']
            game.scenario=form.cleaned_data['scenario']
            game.cell = form.cleaned_data['cell']
            game.invitation_mode = form.cleaned_data['invitation_mode']
            game.list_in_lfg = form.cleaned_data['list_in_lfg']
            game.allow_ringers = form.cleaned_data['allow_ringers']
            game.max_rsvp = form.cleaned_data['max_rsvp']
            game.invite_all_members = form.cleaned_data['invite_all_members']
            game.gametime_url = form.cleaned_data['gametime_url']
            if 'only_over_18' in form.cleaned_data:
                game.is_nsfw = form.cleaned_data['only_over_18']
            if form.cleaned_data['scenario']:
                game.scenario = form.cleaned_data['scenario']
                game.title = game.scenario.title
            with transaction.atomic():
                game.save()
                game.mediums.set(form.cleaned_data['mediums'])
                if hasattr(form.changed_data, 'invite_all_members') and form.cleaned_data['invite_all_members']:
                    for member in game.cell.get_unbanned_members().exclude(member_player=game.gm):
                        game_invite = Game_Invite(invited_player=member.member_player,
                                                  relevant_game=game,
                                                  invite_text=game.hook,
                                                  as_ringer=False)
                        game_invite.save()
                        game_invite.notify_invitee(request, game)
                if changed_start:
                    GameChangeStartTime.send_robust(sender=None, game=game, request=request)
                    post_game_webhook(game, request, is_changed_start=True)
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            logger.error('Error: invalid GameForm. Errors: %s', str(form.errors))
            raise ValueError("Invalid game form")
    else:
        # Build a game form.
        form = GameForm(initial=initial_data)
        scenarios_by_cells = get_scenarios_by_cells(request)
        context = {
            'game': game,
            'scenarios_by_cells': scenarios_by_cells,
            'form' : form,
        }
        return render(request, 'games/edit_game.html', context)


def view_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    my_invitation = None
    user_membership = None
    if request.user.is_authenticated and game.cell:
        user_membership = game.cell.get_player_membership(request.user)
        my_invitation = get_object_or_none(request.user.game_invite_set.filter(relevant_game=game_id))
    community_link = None
    discord_link = False
    if game.cell:
        can_view_community_link = game.cell.is_community_link_public or user_membership
        community_link = game.cell.community_link if can_view_community_link else None
        if community_link:
            discord_link = game.cell.community_link_is_discord()
    scenario_spoiled = game.scenario.player_is_spoiled(request.user)
    invite_form = None
    can_edit = game.player_can_edit(request.user)
    if can_edit and game.is_scheduled():
        initial_data = {"message": game.hook}
        invite_form = CustomInviteForm(initial=initial_data)
    nsfw_blocked = game.is_nsfw and (request.user.is_anonymous or not request.user.profile.view_adult_content)
    reason_cannot_rsvp = game.reason_player_cannot_rsvp(request.user)
    can_rsvp = not reason_cannot_rsvp

    gametime_url = None if not my_invitation or not game.gametime_url else game.gametime_url
    context = {
        'game': game,
        'scenario_spoiled': scenario_spoiled,
        'my_invitation': my_invitation,
        'invite_form': invite_form,
        'can_edit': can_edit,
        'can_rsvp': can_rsvp,
        'reason_cannot_rsvp': reason_cannot_rsvp,
        'nsfw_blocked': nsfw_blocked,
        'gametime_url': gametime_url,
        'community_link': community_link,
        'is_discord_link': discord_link,
    }
    return render(request, 'games/view_game_pages/view_game.html', context)


@login_required
def cancel_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        if not game.player_can_edit(request.user):
            raise PermissionDenied("You don't have permission to edit this Game event")
        if not game.is_scheduled() and not game.is_active():
            raise PermissionDenied("You cannot cancel a game that has been completed")
        with transaction.atomic():
            game.transition_to_canceled()
        return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
    else:
        if not game.player_can_edit(request.user):
            raise PermissionDenied("You don't have permission to edit this Game event")
        context = {
            'game': game,
        }
        return render(request, 'games/cancel_game.html', context)


@login_required
def invite_players(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if not game.player_can_edit(request.user) or not game.is_scheduled():
        raise PermissionDenied("You don't have permission to edit this Game event, or it has already started")
    initial_data = {"message": game.hook}
    if request.method == 'POST':
        form = CustomInviteForm(request.POST, initial=initial_data)
        if form.is_valid():
            player = get_object_or_404(User, username__iexact= form.cleaned_data['username'])
            invite = player.game_invite_set.filter(relevant_game=game).first()
            if invite:
                with transaction.atomic():
                    invite.as_ringer = form.cleaned_data['invite_as_ringer']
                    invite.invite_text = form.cleaned_data['message']
                    invite.save()
                return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
            if player == game.creator or player == game.gm:
                raise PermissionDenied("You can't invite Players to a Game they created or are running.")
            game_invite = Game_Invite(invited_player=player,
                                      relevant_game=game,
                                      invite_text=form.cleaned_data['message'],
                                      as_ringer=form.cleaned_data['invite_as_ringer'])
            with transaction.atomic():
                game_invite.save()
                game_invite.notify_invitee(request, game)
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            logger.error('Error: invalid CustomInviteForm. Errors: %s', str(form.errors))
            raise ValueError("Invalid CustomInviteForm form")
    else:
        return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))


@login_required
def accept_invite(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if not game.player_can_rsvp(request.user):
        raise PermissionDenied(game.reason_player_cannot_rsvp(request.user))
    invite = get_object_or_none(request.user.game_invite_set.filter(relevant_game=game.id))
    if request.method == 'POST':
        if not invite:
            # player self-invite
            invite = Game_Invite(invited_player=request.user,
                                 relevant_game=game)
            if game.scenario in request.user.scenario_set.all():
                invite.as_ringer = True
        form = make_accept_invite_form(invite)(request.POST)
        if form.is_valid():
            game_attendance = invite.attendance
            with transaction.atomic():
                invite.save()
                if game_attendance:
                    changed_character = 'attending_character' in form.cleaned_data and form.cleaned_data['attending_character'] is not None \
                                        and game_attendance.attending_character != form.cleaned_data['attending_character']
                    game_attendance.attending_character = form.cleaned_data['attending_character']
                    game_attendance.save()
                    if changed_character:
                        Notification.objects.create(
                            user=game.gm,
                            headline="Player changed Contractor",
                            content="{} will play {}".format(request.user.username, game_attendance.attending_character.name),
                            url=reverse('games:games_view_game', args=(game.id,)),
                            notif_type=CONTRACT_NOTIF)
                else:
                    game_attendance = Game_Attendance(
                        attending_character=form.cleaned_data['attending_character'],
                        relevant_game=game,
                    )
                    game_attendance.save()
                    invite.is_declined = False
                    invite.attendance = game_attendance
                    invite.save()
                    if invite.as_ringer and not form.cleaned_data['attending_character']:
                        #Reveal scenario to ringer
                        game.scenario.unlocked_discovery(request.user)
                    Notification.objects.create(
                        user=game.gm,
                        headline="Player RSVPed to your Contract",
                        content="{} wants to attend {}".format(request.user.username, game.scenario.title),
                        url=reverse('games:games_view_game', args=(game.id,)),
                        notif_type=CONTRACT_NOTIF)
            cell_membership = game.cell.get_player_membership(request.user)
            cell_invite = get_object_or_none(game.cell.open_invitations().filter(invited_player=request.user))
            if game.cell and not cell_membership and (game.cell.allow_self_invites or cell_invite):
                return HttpResponseRedirect(reverse('cells:cells_rsvp_invite_contract', args=(game.cell.id, game.id,)))
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            logger.error('Error: invalid accept_invite_form. Errors: %s', str(form.errors))
            raise ValueError("Invalid accept_invite_form form")
    else:
        scenario_spoiled = game.scenario.player_is_spoiled(request.user)
        # Build a accept form.
        if not invite:
            # if game is open for self-invites, make a temp invite that we don't save so we can make a form
            invite = Game_Invite(invited_player=request.user,
                                 relevant_game=game)
            if scenario_spoiled:
                invite.as_ringer = True
        form = make_accept_invite_form(invite)
        context = {
            'form': form,
            'game': game,
            'invite': invite,
            'scenario_spoiled': scenario_spoiled,
        }
        return render(request, 'games/accept_invite.html', context)


@login_required
def decline_invite(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if game.is_scheduled():
        invite = get_object_or_none(request.user.game_invite_set.filter(relevant_game=game))
        if not invite:
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        if request.user == invite.invited_player:
            invite.is_declined = True
            if invite.attendance:
                invite.attendance.delete()
                invite.attendance = None
            with transaction.atomic():
                invite.save()
    return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))


#TODO: Pull some of this into helper functions
#TODO: Enforce or advise on number of players constraints
def start_game(request, game_id, char_error="", player_error=""):
    game = get_object_or_404(Game, id=game_id)
    if not game.player_can_edit(request.user):
        raise PermissionDenied("You don't have permission to edit this Game event")
    if not game.is_scheduled():
        raise PermissionDenied("This Game has already started")
    ValidateAttendanceFormSet = formset_factory(ValidateAttendanceForm, extra=0)
    game_attendances = game.game_attendance_set.all()
    initial_data = []
    for game_attendance in game_attendances:
        initial = {
            'player': game_attendance.game_invite.invited_player.id,
            'attending': True,
            'game_attendance': game_attendance,
        }
        if game_attendance.attending_character:
            initial['character'] = game_attendance.attending_character.id
        initial_data.append(initial)
    if request.method == 'POST':
        if request.POST['form-TOTAL_FORMS'] == '0':
            raise PermissionDenied("Must have at least one Player")

        formset = ValidateAttendanceFormSet(request.POST,
                                            form_kwargs={'game': game},
                                            initial=initial_data)
        if formset.is_valid():
            canceled_players=[]
            changed_character_players=[]
            for form in formset:
                if not form.initial:
                    # if invite canceled. We don't care about inverse where invite accepted after screen
                    canceled_players.append(str(form.cleaned_data["player"].id))
                elif form.cleaned_data['character'] and (form.cleaned_data['character'].id != form.initial['character']):
                    changed_character_players.append(str(form.cleaned_data["player"].id))
                elif form.cleaned_data['player'].id != form.initial['player']:
                    #forged form, changed player invariant check
                    raise PermissionDenied("Stop messing with the forms.")
            if canceled_players or changed_character_players:
                url_kwargs = {'game_id': game.id}
                if changed_character_players:
                    chars = ",".join(changed_character_players)
                    url_kwargs['char_error']=chars
                if canceled_players:
                    playas=  ",".join(canceled_players)
                    url_kwargs['player_error'] = playas
                return HttpResponseRedirect(reverse('games:games_start_game', kwargs=url_kwargs))
            attending_characters = []
            with transaction.atomic():
                for form in formset:
                    if not form.cleaned_data['attending']:
                        game.not_attending(form.cleaned_data['player'])
                    elif form.cleaned_data['character']:
                        attending_characters.append(form.cleaned_data['character'].id)
                if len(attending_characters) == 0:
                    raise PermissionDenied("You can't start a game without any attending Characters!")
                for character in game.attended_by.all():
                    if character.id not in attending_characters:
                        game.not_attending(character.player)
                game.transition_to_active()
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            logger.error('Error: invalid ValidateAttendanceFormSet. Errors: %s', str(formset.errors))
            raise ValueError("Invalid ValidateAttendanceFormSet form")
    else:
        formset = ValidateAttendanceFormSet(form_kwargs={'game': game},
                                              initial=initial_data)
        context = {
            'game': game,
            'formset':formset,
        }
        if char_error:
            error_characters = []
            for character_id in char_error.split(','):
                character = get_object_or_404(User, id=int(character_id))
                error_characters.append(character)
            context['char_errors'] = error_characters
            context['char_error_pids']=char_error.split(',')
        if player_error:
            error_players = []
            for player_id in player_error.split(','):
                player = get_object_or_404(User, id=int(player_id))
                error_players.append(player)
            context['player_errors'] = error_players
        return render(request, 'games/start_game.html', context)


@login_required
def end_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if not game.player_can_edit(request.user):
        raise PermissionDenied("You don't have permission to edi this Game Event")
    if not game.is_active():
        raise PermissionDenied("You can't end a Game event that isn't in progress")
    DeclareOutcomeFormset = formset_factory(DeclareOutcomeForm, extra=0)
    game_attendances = game.game_attendance_set.all()
    initial_data = []
    character_ids = []
    for game_attendance in game_attendances:
        initial = {
            'player': game_attendance.game_invite.invited_player.id,
            'game_attendance': game_attendance,
            'hidden_attendance': game_attendance.id,
        }
        initial_data.append(initial)
        if game_attendance.attending_character:
            character_ids.append(game_attendance.attending_character.pk)
    character_queryset = Character.objects.filter(pk__in=character_ids)
    GrantElementForm = make_grant_element_form(character_queryset)
    GrantElementFormset = formset_factory(GrantElementForm, extra=0)
    scenario = game.scenario
    initial_elements = [{
        "element_id": x.pk,
        "element": x
    } for x in scenario.get_latest_of_all_elements() if not x.is_deleted]
    if request.method == 'POST':
        declare_outcome_formset = DeclareOutcomeFormset(request.POST, initial=initial_data, prefix="outcome")
        game_feedback_form = GameFeedbackForm(request.POST)
        world_event_form = None
        if initial_elements:
            element_formset = GrantElementFormset(request.POST, initial=initial_elements, prefix="elements")
        else:
            element_formset = None
        if game.cell.player_can_post_world_events(request.user):
            world_event_form = EditWorldEventForm(request.POST)
        if declare_outcome_formset.is_valid() and game_feedback_form.is_valid() \
                and (not world_event_form or world_event_form.is_valid())\
                and (not element_formset or element_formset.is_valid()):
            if len([x for x in declare_outcome_formset if x.cleaned_data["MVP"]]) > 1:
                raise ValueError("More than one MVP in completed edit")
            with transaction.atomic():
                game = Game.objects.select_for_update().get(pk=game.pk)
                for form in declare_outcome_formset:
                    attendance = get_object_or_404(Game_Attendance, id=form.cleaned_data['hidden_attendance'].id)
                    if attendance.relevant_game_id != game.pk:
                        raise ValueError("Attendance edited for wrong game!")
                    attendance.outcome = form.cleaned_data['outcome']
                    attendance.is_mvp = form.cleaned_data['MVP']
                    if form.cleaned_data['notes']:
                        attendance.notes = form.cleaned_data['notes']
                    attendance.save()
                if game_feedback_form.cleaned_data['scenario_notes']:
                    game.scenario_notes = game_feedback_form.cleaned_data['scenario_notes']
                if world_event_form and \
                        (world_event_form.cleaned_data['headline'] or world_event_form.cleaned_data['event_description']):
                    world_event = WorldEvent(creator=request.user,
                                             parent_cell=game.cell,)
                    world_event.headline = world_event_form.cleaned_data["headline"] if "headline" in world_event_form.cleaned_data else " "
                    world_event.event_description = world_event_form.cleaned_data["event_description"]
                    world_event.save()
                    webhooks = game.cell.webhook_cell.filter(send_for_events=True).all()
                    for webhook in webhooks:
                        webhook.post_for_event(world_event, request)
                if element_formset:
                    for form in element_formset:
                        element = form.initial["element"]
                        for character in form.cleaned_data["grant_to_characters"]:
                            element.relevant_element.grant_to_character_no_trauma(character, request.user, game.cell)
                game.save()
                game.transition_to_finished()
                GameEnded.send_robust(sender=None, game=game, request=request)
                if game.gm != game.scenario.creator:
                    Notification.objects.create(
                        user=game.scenario.creator,
                        headline="Someone ran your Scenario",
                        content=game.scenario.title,
                        url=reverse('games:games_view_scenario', args=(game.scenario.id,)),
                        notif_type=SCENARIO_NOTIF)
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            logger.error('Error: invalid declare_outcome_formset or game_feedback_form. declare_outcome_formset errors: %s\n\n game_feedback_form errors: %s',
                         str(declare_outcome_formset.errors),
                         str(game_feedback_form.errors))
            raise ValueError("Invalid form")
    else:
        formset = DeclareOutcomeFormset(initial=initial_data, prefix="outcome")
        element_formset = GrantElementFormset(initial=initial_elements, prefix="elements")
        game_feedback = GameFeedbackForm()
        world_event_form = None
        if game.cell.player_can_post_world_events(request.user):
            world_event_form = EditWorldEventForm()
        context = {
            'formset': formset,
            'feedback_form': game_feedback,
            'world_event_form': world_event_form,
            'game': game,
            'element_formset': element_formset if len(initial_elements) > 0 else None,
        }
        return render(request, 'games/end_game.html', context)


@login_required
def allocate_improvement_generic(request):
    avail_improvements = request.user.profile.get_avail_improvements()
    if len(avail_improvements) > 0:
        return HttpResponseRedirect(reverse('games:games_allocate_improvement', args=(avail_improvements.first().id,)))
    else:
        return HttpResponseRedirect(reverse('home', args=()))


@login_required
def allocate_improvement(request, improvement_id):
    improvement = get_object_or_404(Reward, id=improvement_id)
    if not improvement.is_improvement or improvement.rewarded_character:
        raise PermissionDenied("Either this Reward isn't an improvement, or it's already been allocated")
    if not request.user.is_authenticated or not improvement.rewarded_player.id == request.user.id:
        raise PermissionDenied("You must log in, or you can only allocate your own rewards")
    if request.method == 'POST':
        form = make_allocate_improvement_form(request.user)(request.POST)
        if form.is_valid():
            improvement.rewarded_character = form.cleaned_data['chosen_character']
            with transaction.atomic():
                improvement.save()
            return HttpResponseRedirect(reverse('characters:characters_spend_reward', args=(form.cleaned_data['chosen_character'].id,)))
        else:
            print(form.errors)
            return None
    else:
        form = make_allocate_improvement_form(request.user)()
        context = {
            'form': form,
            'improvement': improvement,
        }
        return render(request, 'games/allocate_improvement.html', context)


# Select which players attended and who was GM
@login_required
def create_ex_game_for_cell(request, cell_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must log in to create archival Contract events")
    cell = get_object_or_404(Cell, id = cell_id)
    if not cell.player_can_manage_games(request.user):
        raise PermissionDenied("You do not have permission to manage Contract Events for this Cell")
    if request.method == 'POST':
        gm_form = get_gm_form(cell, request.POST)
        outsider_formset = get_outsider_formset(request.POST)
        member_formset = get_member_formset(cell, POST=request.POST)
        if gm_form.is_valid() and member_formset.is_valid() and outsider_formset.is_valid():
            gm = get_object_or_404(User, username=gm_form.cleaned_data['gm'])
            players = get_players_for_new_attendances(member_formset, outsider_formset)
            return HttpResponseRedirect(
                reverse('games:games_edit_ex_game_add_players', args=(cell.id, gm.id, '+'.join(players),)))
        else:
            logger.error('Error: invalid forms. GM Errors: %s\n\noutsider errors %s\n\n member errors: %s',
                         str(gm_form.errors),
                         str(outsider_formset.errors),
                         str(member_formset.errors))
            raise ValueError("Invalid form")
    else:
        context = get_context_for_choose_attending(cell)
        return render(request, 'games/create_ex_game_choose_attendance.html', context)


@login_required
def finalize_create_ex_game_for_cell(request, cell_id, gm_user_id, players):
    if not request.user.is_authenticated:
        raise PermissionDenied("Log in, yo")
    cell = get_object_or_404(Cell, id = cell_id)
    if not cell.player_can_manage_games(request.user):
        raise PermissionDenied("You do not have permission to manage Game Events for this Cell")
    gm = get_object_or_404(User, id=gm_user_id)
    player_list = [get_object_or_404(User, id=player_id) for player_id in players.split('+') if not player_id == str(gm.id)]
    GenInfoForm = make_archive_game_general_info_form(gm)
    ArchivalOutcomeFormSet = formset_factory(get_archival_outcome_form(EXP_V1_V2_GAME_ID+1), extra=0)
    if request.method == 'POST':
        general_form = GenInfoForm(request.POST, prefix="general")
        outcome_formset = ArchivalOutcomeFormSet(request.POST, prefix="outcome", initial=[{'player_id': x.id,
                                                           'invited_player': x}
                                                          for x in player_list])
        if general_form.is_valid() and outcome_formset.is_valid():
            create_archival_game(request, general_form, cell, outcome_formset)
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(cell.id,)))
        else:
            logger.error('Error: invalid forms. general_form Errors: %s\n\noutcome_formset errors: %s',
                         str(general_form.errors),
                         str(outcome_formset.errors))
            raise ValueError("Invalid form")
    else:
        context = get_context_for_create_finished_game(player_list, players, gm, cell, GenInfoForm, ArchivalOutcomeFormSet)
        return render(request, 'games/edit_archive_game.html', context)


# Choose additional players to add to a completed game.
@login_required
def add_attendance(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    _check_perms_for_edit_completed(request, game)
    cell = game.cell
    if request.method == 'POST':
        outsider_formset = get_outsider_formset(request.POST)
        member_formset = get_member_formset(cell, POST=request.POST)
        if member_formset.is_valid() and outsider_formset.is_valid():
            players = get_players_for_new_attendances(member_formset, outsider_formset)
            return HttpResponseRedirect(
                reverse('games:games_edit_completed', args=(game_id, '+'.join(players),)))
        else:
            logger.error('Error: invalid forms. outsider_formset Errors: %s\n\nmember_formset errors: %s',
                         str(outsider_formset.errors),
                         str(member_formset.errors))
            raise ValueError("Invalid add attendance form")
    else:
        context = get_context_for_choose_attending(cell, game)
        return render(request, 'games/create_ex_game_choose_attendance.html', context)



@login_required
def edit_completed(request, game_id, players = None):
    game = get_object_or_404(Game, id=game_id)
    _check_perms_for_edit_completed(request, game)
    new_player_list = [get_object_or_404(User, id=player_id) for player_id in players.split('+')] if players else []
    if request.method == 'POST':
        handle_edit_completed_game(request, game, new_player_list)
        return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
    else:
        context = get_context_for_completed_edit(game, new_player_list, players)
        return render(request, 'games/edit_archive_game.html', context)


def _check_perms_for_edit_completed(request, game):
    if request.user.is_superuser:
        return
    if not request.user.is_authenticated:
        raise PermissionDenied("You must log in.")
    if not (game.is_finished() or game.is_archived() or game.is_recorded()):
        raise PermissionDenied("You can't add an attendance to a Game that isn't finished.")
    if not game.player_can_edit(request.user):
        raise PermissionDenied("You don't have permission to edit this Game")


@login_required
def confirm_attendance(request, attendance_id, confirmed=None):
    if not request.user.is_authenticated:
        raise PermissionDenied("You gotta log in")
    attendance = get_object_or_404(Game_Attendance, id=attendance_id)
    if not request.user.id == attendance.game_invite.invited_player.id:
        raise PermissionDenied("Wait, you're not the person I was talking about 0.o")
    if request.method == 'POST':
        if confirmed is None:
            return render_confirm_attendance_page(request, attendance)
        form = RsvpAttendanceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if confirmed == 'y':
                    attendance.confirm_and_reward()
                    attendance.relevant_game.update_profile_stats()
                    if hasattr(attendance, "attending_character") and attendance.attending_character:
                        attendance.attending_character.progress_loose_ends(attendance.relevant_game.actual_start_time)
                else:
                    invite = attendance.game_invite
                    invite.is_declined = True
                    invite.save()
        else:
            logger.error('Error: invalid confirm attendance form. Errors: %s',
                         str(form.errors))
            raise ValueError("Invalid confirm attendance form")
        return HttpResponseRedirect(reverse('games:games_view_game', args=(attendance.relevant_game.id,)))
    else:
        return render_confirm_attendance_page(request, attendance)


@login_required
def render_confirm_attendance_page(request, attendance):
    form = RsvpAttendanceForm()
    context = {
        'form': form,
        'attendance': attendance,
    }
    return render(request, 'games/confirm_attendance.html', context)


@login_required
def spoil_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not scenario.is_spoilable_for_player(request.user):
        return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
    if request.method == 'POST':
        form = SpoilScenarioForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                scenario.spoil_already_discovered(request.user)
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            raise ValueError("Invalid aftermath spoil form")
    else:
        context = {
            "scenario": scenario,
            "spoil_form": SpoilScenarioForm(),
        }
        return render(request, 'games/scenarios/spoil_scenario.html', context)


class LookingForGame(View):
    template_name = 'games/looking_for_game.html'

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __get_context_data(self):
        now = datetime.datetime.now()
        two_hours_ago = now - datetime.timedelta(hours=2)
        two_weeks_ago = now - datetime.timedelta(weeks=2)
        games_query = Game.objects.filter(
            list_in_lfg=True,
            status=GAME_STATUS[0][0],
            scheduled_start_time__gte=two_hours_ago)
        if self.request.user.is_anonymous or not self.request.user.profile.view_adult_content:
            games_query = games_query.exclude(is_nsfw=True)
        games = games_query.order_by('scheduled_start_time').all()
        completed_games_query = Game.objects.filter(
            list_in_lfg=True,
            status=GAME_STATUS[2][0],
            end_time__gte=two_weeks_ago)
        if self.request.user.is_anonymous or not self.request.user.profile.view_adult_content:
            completed_games_query = completed_games_query.exclude(is_nsfw=True)
        completed_games = completed_games_query.order_by('-end_time').all()
        context = {
            'games': games,
            'completed_games': completed_games,
        }
        return context


# MOVES
@method_decorator(login_required(login_url='account_login'), name='dispatch')
class ViewMove(View):
    template_name = 'games/moves/view_move.html'
    move = None

    def dispatch(self, *args, **kwargs):
        self.move = get_object_or_404(Move, id=self.kwargs['move_id'])
        redirect = self.__check_permissions()
        if redirect:
            return redirect
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __check_permissions(self):
        if not self.move.main_character.player_can_view(self.request.user):
            raise PermissionDenied("You do not have permission to view this contractor")

    def __get_context_data(self):
        self.cell = self.move.cell
        can_edit = self.cell.player_can_run_games(self.request.user) and self.cell.player_can_post_world_events(self.request.user)
        context = {
            'move': self.move,
            'player_can_edit': can_edit,
        }
        return context


class EnterMove(View):
    event_form_class = EditWorldEventForm
    move_form_class = None
    template_name = 'games/moves/edit_move.html'
    initial_move = None
    initial_event = None
    world_event = None
    move = None
    cell = None
    character = None

    def dispatch(self, *args, **kwargs):
        redirect = self.__check_permissions()
        if redirect:
            return redirect
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        event_form = self.event_form_class(request.POST)
        move_form = self.move_form_class(request.POST)
        if event_form.is_valid() and move_form.is_valid():
            with transaction.atomic():
                new_event = self.world_event is None
                if new_event:
                    self.world_event = WorldEvent(creator=request.user,
                                                  parent_cell=self.cell,
                                                  )
                else:
                    self.world_event = WorldEvent.objects.select_for_update().get(pk=self.world_event.pk)
                self.world_event.headline = event_form.cleaned_data["headline"] if "headline" in event_form.cleaned_data else " "
                self.world_event.event_description = event_form.cleaned_data["event_description"]
                self.world_event.save()

                move_char = self.character if self.character else move_form.cleaned_data["character"]
                if self.move is None:
                    self.move = Move(gm=self.request.user,
                                     downtime=move_char.get_current_downtime_attendance(),
                                     cell=self.cell,
                                     public_event=self.world_event,
                                     main_character=move_char,
                                     )
                else:
                    self.move = Move.objects.select_for_update().get(pk=self.move.pk)
                self.move.title = move_form.cleaned_data["title"]
                self.move.summary = move_form.cleaned_data["summary"]
                self.move.is_private = move_form.cleaned_data["is_private"]
                self.move.save()

                if new_event:
                    self.move.gm.profile.update_move_stat()
                    webhooks = self.cell.webhook_cell.filter(send_for_events=True).all()
                    for webhook in webhooks:
                        webhook.post_for_event(self.world_event, request, self.move)
                    for membership in self.cell.get_unbanned_members():
                        Notification.objects.create(
                            user=membership.member_player,
                            headline="A Contractor made a Move",
                            content="In {}".format(self.cell.name),
                            url=reverse('games:view_move', args=(self.move.id,)),
                            notif_type=WORLD_NOTIF,
                            is_timeline=True,
                            article=self.world_event)
            return HttpResponseRedirect(reverse('games:view_move', args=(self.move.id,)))
        raise ValueError("Invalid Move or event form")

    def __check_permissions(self):
        if self.character:
            if not self.character.cell:
                raise PermissionDenied("Contractors must be a part of a Playgroup to make Moves.")
            if self.character.num_games == 0:
                raise PermissionDenied("Only Contractors who have participated in at least one Contract can make Moves.")
        if not self.cell.player_can_run_games(self.request.user):
            raise PermissionDenied("You must have permissions to run Contracts in this Playgroup to GM Moves.")
        if not self.cell.player_can_post_world_events(self.request.user):
            raise PermissionDenied("You must have permissions to post world events in this Playgroup to GM Moves.")

    def __get_context_data(self):
        context = {
            'character': self.character,
            'move': self.move,
            'cell': self.cell,
            'move_form': self.move_form_class(initial=self.initial_move),
            'event_form': self.event_form_class(initial=self.initial_event),
        }
        return context


class CreateMoveCell(EnterMove):

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            raise PermissionDenied("Must log in to create a move")
        self.cell = get_object_or_404(Cell, id=self.kwargs['cell_id'])
        self.move_form_class = make_edit_move_form(self.request.user, cell=self.cell)
        return super().dispatch(*args, **kwargs)


class CreateMoveChar(EnterMove):

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            raise PermissionDenied("Must log in to create a move")
        self.character = get_object_or_404(Character, id=self.kwargs['character_id'])
        self.cell = self.character.cell
        self.move_form_class = make_edit_move_form(self.request.user)
        return super().dispatch(*args, **kwargs)


class EditMove(EnterMove):

    def dispatch(self, *args, **kwargs):
        self.move = get_object_or_404(Move, id=self.kwargs['move_id'])
        self.world_event = self.move.public_event
        self.character = self.move.main_character
        self.cell = self.move.cell
        self.move_form_class = make_edit_move_form(self.move.gm)
        self.initial_move = {
            "title": self.move.title,
            "summary": self.move.summary,
        }
        self.initial_event = {
            "headline": self.world_event.headline,
            "event_description": self.world_event.event_description,
        }
        return super().dispatch(*args, **kwargs)