from django.contrib.auth.models import User
from django.forms import formset_factory
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, _get_queryset
from django.db import transaction

# Create your views here.
from django.urls import reverse
from django.utils import timezone
from games.forms import CreateScenarioForm

from games.models import Scenario, Game, GAME_STATUS, DISCOVERY_REASON

from games.forms import make_game_form, make_allocate_improvement_form, CustomInviteForm, make_accept_invite_form, ValidateAttendanceForm, DeclareOutcomeForm, GameFeedbackForm

from games.models import Game_Invite

from hgapp.utilities import get_queryset_size

from games.models import Game_Attendance, Reward

from hgapp.utilities import get_object_or_none

from cells.models import Cell

from characters.models import HIGH_ROLLER_STATUS


def create_scenario(request):
    if request.method == 'POST':
        form = CreateScenarioForm(request.POST)
        if form.is_valid():
            scenario = Scenario(
                title = form.cleaned_data['title'],
                creator = request.user,
                summary = form.cleaned_data['summary'],
                description = form.cleaned_data['description'],
                max_players = form.cleaned_data['max_players'],
                min_players = form.cleaned_data['min_players'],
                suggested_status = form.cleaned_data['suggested_character_status'],
                is_highlander = form.cleaned_data['is_highlander'],
                requires_ringer= form.cleaned_data['requires_ringer'],
                is_rivalry = form.cleaned_data['is_rivalry']
            )
            scenario.save()
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a scenario form.
        form = CreateScenarioForm()
        context = {
            'form' : form,
        }
        return render(request, 'games/edit_scenario.html', context)

def edit_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not request.user.has_perm('edit_scenario', scenario):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = CreateScenarioForm(request.POST)
        if form.is_valid():
            scenario.title=form.cleaned_data['title']
            scenario.summary=form.cleaned_data['summary']
            scenario.description=form.cleaned_data['description']
            scenario.max_players=form.cleaned_data['max_players']
            scenario.min_players=form.cleaned_data['min_players']
            scenario.suggested_status=form.cleaned_data['suggested_character_status']
            scenario.is_highlander=form.cleaned_data['is_highlander']
            scenario.is_rivalry=form.cleaned_data['is_rivalry']
            scenario.requires_ringer=form.cleaned_data['requires_ringer']
            scenario.pub_date=timezone.now()
            scenario.save()
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a scenario form.
        form = CreateScenarioForm(initial={'title': scenario.title,
                                            'summary': scenario.summary,
                                            'description': scenario.description,
                                            'max_players': scenario.max_players,
                                            'min_players': scenario.min_players,
                                            'suggested_character_status': scenario.suggested_status,
                                            'is_highlander': scenario.is_highlander,
                                            'is_rivalry': scenario.is_rivalry,
                                            'requires_ringer': scenario.requires_ringer})
        context = {
            'scenario': scenario,
            'form' : form,
        }
        return render(request, 'games/edit_scenario.html', context)

def view_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not request.user.has_perm("view_scenario", scenario):
        return HttpResponseForbidden()
    context = {
        'scenario': scenario,
    }
    return render(request, 'games/view_scenario.html', context)

def view_scenario_gallery(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    owned_scenarios = request.user.scenario_creator.all()
    discovered_scenarios = request.user.scenario_discovery_set.exclude(reason=DISCOVERY_REASON[1][0]).all()
    context = {
        'owned_scenarios': owned_scenarios,
        'scenario_discoveries': discovered_scenarios,
    }
    return render(request, 'games/view_scenario_gallery.html', context)

def create_game(request):
    if request.method == 'POST':
        form = make_game_form(user=request.user, game_status=GAME_STATUS[0][0])(request.POST)
        if form.is_valid():
            game = Game(
                title = form.cleaned_data['title'],
                creator = request.user,
                gm = request.user,
                required_character_status = form.cleaned_data['required_character_status'],
                hook = form.cleaned_data['hook'],
                created_date = timezone.now(),
                scheduled_start_time = form.cleaned_data['scheduled_start_time'],
                open_invitations = form.cleaned_data['open_invitations'],
                status = GAME_STATUS[0][0],
                cell = form.cleaned_data['cell']
            )
            if form.cleaned_data['scenario']:
                game.scenario = form.cleaned_data['scenario']
            else:
                scenario = Scenario(creator=request.user,
                                    title="Temporary Scenario for " + game.title,
                                    description="Put details of the scenario here",
                                    suggested_status=HIGH_ROLLER_STATUS[0][0],
                                    max_players=99,
                                    min_players=0)
                scenario.save()
                game.scenario = scenario
            with transaction.atomic():
                game.save()
                if form.cleaned_data['invite_all_members']:
                    for member in game.cell.cellmembership_set.exclude(member_player = game.creator):
                        invite = str(game.creator) + " has invited you to a Game in " + game.cell.name
                        game_invite = Game_Invite(invited_player=member.member_player,
                                                  relevant_game=game,
                                                  invite_text=invite,
                                                  as_ringer=False)
                        game_invite.save()
            return HttpResponseRedirect(reverse('games:games_invite_players', args=(game.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a game form.
        form = make_game_form(user=request.user, game_status=GAME_STATUS[0][0])
        context = {
            'form' : form,
        }
        return render(request, 'games/edit_game.html', context)

def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        if not request.user.has_perm('edit_game', game):
            return HttpResponseForbidden()
        form = make_game_form(user=request.user, game_status=game.required_character_status)(request.POST)
        if form.is_valid():
            game.title=form.cleaned_data['title']
            game.hook=form.cleaned_data['hook']
            if game.is_scheduled():
                game.open_invitations = form.cleaned_data['open_invitations']
                game.scheduled_start_time = form.cleaned_data['scheduled_start_time']
                game.required_character_status = form.cleaned_data['required_character_status']
                game.scenario=form.cleaned_data['scenario']
                game.cell = form.cleaned_data['cell']
                if form.cleaned_data['scenario']:
                    game.scenario = form.cleaned_data['scenario']
            with transaction.atomic():
                game.save()
                if form.cleaned_data['invite_all_members']:
                    for member in game.cell.cellmembership_set.exclude(member_player=game.creator):
                        invite = game.creator.name + " has invited you to a Game in " + game.cell.name
                        game_invite = Game_Invite(invited_player=member.member_player,
                                                  relevant_game=game,
                                                  invite_text=invite,
                                                  as_ringer=False)
                        game_invite.save()
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a game form.
        form = make_game_form(user=request.user, game_status=game.status)(initial={'title': game.title,
                                                                                   'hook': game.hook,
                                                                                   'scenario': game.scenario,
                                                                                   'required_character_status': game.required_character_status,
                                                                                   'start_time': game.scheduled_start_time,
                                                                                   'cell': game.cell,
                                                                                   })
        context = {
            'game': game,
            'form' : form,
        }
        return render(request, 'games/edit_game.html', context)

def view_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    view_scenario = False
    invitation = None
    if request.user.is_authenticated:
        invitation = get_object_or_none(request.user.game_invite_set.filter(relevant_game=game_id))
    if request.user.has_perm("view_scenario", game.scenario):
        view_scenario = True
    context = {
        'game': game,
        'view_scenario': view_scenario,
        'invitation': invitation,
    }
    return render(request, 'games/view_game_pages/view_game.html', context)

#TODO: if game is active, add option to share scenario with participants
def cancel_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        if not request.user.has_perm('edit_game', game):
            return HttpResponseForbidden()
        if not game.is_scheduled() and not game.is_active():
            return HttpResponseForbidden()
        game.transition_to_canceled()
        return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
    else:
        if not request.user.has_perm('edit_game', game):
            return HttpResponseForbidden()
        context = {
            'game': game,
        }
        return render(request, 'games/cancel_game.html', context)

def invite_players(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if not request.user.has_perm('edit_game', game) or not game.is_scheduled():
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = CustomInviteForm(request.POST)
        if form.is_valid():
            player = get_object_or_404(User, username__iexact= form.cleaned_data['username'])
            if get_queryset_size(player.game_invite_set.filter(relevant_game=game)) > 0:
                #player is already invited. Maybe update invitation instead?
                return HttpResponseForbidden()
            if player == game.creator:
                return HttpResponseForbidden()
            game_invite = Game_Invite(invited_player=player,
                                      relevant_game=game,
                                      invite_text=form.cleaned_data['message'],
                                      as_ringer=form.cleaned_data['invite_as_ringer'])
            game_invite.save()
            #Do invite shit, notify player in the model create method.
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            print(form.errors)
            return None
    else:
        form = CustomInviteForm()
        context = {
            'form':form,
            'game':game,
        }
        return render(request, 'games/invite_players.html', context)

def accept_invite(request, game_id):
    if not request.user.is_authenticated or request.user.is_anonymous:
        return HttpResponseForbidden()
    game = get_object_or_404(Game, id=game_id)
    if not game.is_scheduled() or game.creator.id == request.user.id:
        return HttpResponseForbidden()
    invite = get_object_or_none(request.user.game_invite_set.filter(relevant_game=game))
    if not invite and not game.open_invitations:
        return HttpResponseForbidden()
    if request.method == 'POST':
        if not invite:
            # player self-invite
            invite = Game_Invite(invited_player=request.user,
                                 relevant_game=game)
            if game.scenario in request.user.scenario_set.all():
                invite.as_ringer = True
            invite.save()
        form =  make_accept_invite_form(invite)(request.POST)
        if form.is_valid():
            game_attendance = invite.attendance
            if game_attendance:
                game_attendance.attending_character=form.cleaned_data['attending_character']
                game_attendance.save()
            else:
                game_attendance = Game_Attendance(
                    attending_character=form.cleaned_data['attending_character'],
                    relevant_game=game,
                )
                game_attendance.save()
                invite.is_declined = False
                invite.attendance = game_attendance
                invite.save()
                if invite.as_ringer:
                    #Reveal scenario to ringer
                    game.scenario.played_discovery(request.user)
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a accept form.
        if not invite:
            # if game is open for self-invites, make a temp invite that we don't save so we can make a form
            invite = Game_Invite(invited_player=request.user,
                                 relevant_game=game)
            if game.scenario in request.user.scenario_set.all():
                invite.as_ringer = True
        form = make_accept_invite_form(invite)
        context = {
            'form': form,
            'game': game,
            'invite': invite,
        }
        return render(request, 'games/accept_invite.html', context)

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
            invite.save()
    return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))

#TODO: Pull some of this into helper functions
#TODO: Enforce or advise on number of players constraints
def start_game(request, game_id, char_error=" ", player_error=" "):
    game = get_object_or_404(Game, id=game_id)
    if not request.user.has_perm('edit_game', game):
        return HttpResponseForbidden()
    if not game.is_scheduled:
        return HttpResponseForbidden()
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
            return HttpResponseForbidden()

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
                    return HttpResponseForbidden()
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
            for form in formset:
                if not form.cleaned_data['attending']:
                    game.not_attending(form.cleaned_data['player'])
                elif form.cleaned_data['character']:
                    attending_characters.append(form.cleaned_data['character'].id)
            if len(attending_characters) == 0:
                return HttpResponseForbidden()
            for character in game.attended_by.all():
                if character.id not in attending_characters:
                    game.not_attending(character.player)
            game.transition_to_active(lock_characters=False)
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            print(formset.errors)
            return None
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

def end_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if not request.user.has_perm('edit_game', game):
        return HttpResponseForbidden()
    if not game.is_active:
        return HttpResponseForbidden()
    DeclareOutcomeFormset = formset_factory(DeclareOutcomeForm, extra=0)
    game_attendances = game.game_attendance_set.all()
    initial_data = []
    for game_attendance in game_attendances:
        initial = {
            'player': game_attendance.game_invite.invited_player.id,
            'game_attendance': game_attendance,
            'hidden_attendance': game_attendance.id,
        }
        initial_data.append(initial)
    if request.method == 'POST':
        declare_outcome_formset = DeclareOutcomeFormset(request.POST,
                                            initial=initial_data)
        game_feedback_form = GameFeedbackForm(request.POST)
        if declare_outcome_formset.is_valid() and game_feedback_form.is_valid():
            for form in declare_outcome_formset:
                attendance = get_object_or_404(Game_Attendance, id=form.cleaned_data['hidden_attendance'].id)
                attendance.outcome = form.cleaned_data['outcome']
                if form.cleaned_data['notes']:
                    attendance.notes = form.cleaned_data['notes']
                attendance.save()
            if game_feedback_form.cleaned_data['scenario_notes']:
                game.scenario_notes = game_feedback_form.cleaned_data['scenario_notes']
            game.save()
            game.transition_to_finished()
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            print(declare_outcome_formset.errors + game_feedback_form.errors)
            return None
    else:
        formset = DeclareOutcomeFormset(initial=initial_data)
        game_feedback = GameFeedbackForm()
        context = {
            'formset':formset,
            'feedback_form':game_feedback,
            'game':game,
        }
        return render(request, 'games/end_game.html', context)

def allocate_improvement_generic(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    avail_improvements = request.user.rewarded_player.filter(rewarded_character=None).filter(is_void=False).all()
    if len(avail_improvements) > 0:
        return HttpResponseRedirect(reverse('games:games_allocate_improvement', args=(avail_improvements.first().id,)))
    else:
        return HttpResponseRedirect(reverse('hgapp:home', args=()))



def allocate_improvement(request, improvement_id):
    improvement = get_object_or_404(Reward, id=improvement_id)
    if not improvement.is_improvement or improvement.rewarded_character:
        return HttpResponseForbidden()
    if not request.user.is_authenticated or not improvement.rewarded_player.id == request.user.id:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = make_allocate_improvement_form(request.user)(request.POST)
        if form.is_valid():
            improvement.rewarded_character = form.cleaned_data['chosen_character']
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


def create_ex_game_for_cell(request, cell_id):
    cell = get_object_or_404(Cell, id = cell_id)
    pass


def finalize_create_ex_game_for_cell(request, cell_id, gm_user_id, players):
    pass