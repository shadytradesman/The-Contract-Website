from django.contrib.auth.models import User
from django.forms import formset_factory
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.contrib import messages

from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from games.forms import CreateScenarioForm, CellMemberAttendedForm, make_game_form, make_allocate_improvement_form, \
    CustomInviteForm, make_accept_invite_form, ValidateAttendanceForm, DeclareOutcomeForm, GameFeedbackForm, \
    OutsiderAttendedForm, make_who_was_gm_form,make_archive_game_general_info_form, ArchivalOutcomeForm, \
    RsvpAttendanceForm

from .game_form_utilities import get_context_for_create_finished_game, change_time_to_current_timezone, convert_to_localtime, \
    create_archival_game, get_context_for_completed_edit, handle_edit_completed_game, get_context_for_choose_attending, \
    get_gm_form, get_outsider_formset, get_member_formset, get_players_for_new_attendances
from .games_constants import GAME_STATUS



from games.models import Scenario, Game, DISCOVERY_REASON, Game_Invite, Game_Attendance, Reward

from hgapp.utilities import get_queryset_size, get_object_or_none

from cells.models import Cell


def enter_game(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to enter a Game")
    cells = [cell for cell in request.user.cell_set.all() if cell.player_can_manage_games(request.user)]
    context = {
        'cells' : cells,
    }
    return render(request, 'games/enter_game.html', context)


def create_scenario(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to create a Scenario")
    if not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
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
            with transaction.atomic():
                scenario.save()
                if request.user.is_superuser:
                    scenario.tags.set(form.cleaned_data["tags"])
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
        raise PermissionDenied("You don't have permission to edit this scenario")
    if not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
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
            with transaction.atomic():
                scenario.save()
                if request.user.is_superuser:
                    scenario.tags.set(form.cleaned_data["tags"])
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
                                            'requires_ringer': scenario.requires_ringer,
                                            'tags': scenario.tags.all(),
                                           })
        context = {
            'scenario': scenario,
            'form' : form,
        }
        return render(request, 'games/edit_scenario.html', context)

def view_scenario(request, scenario_id, game_id=None):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if not scenario.player_can_view(request.user):
        raise PermissionDenied("You don't have permission to view this scenario")
    show_spoiler_warning = scenario.is_public() and \
                           not (request.user.is_authenticated and scenario.player_discovered(request.user))
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
        game_feedback = None
        games_run = Game.objects.filter(gm_id=request.user.id, scenario_id=scenario.id).all()
        games_run = [x for x in games_run if not x.is_scheduled() and not x.is_active()]
        games_run_no_feedback = Game.objects.filter(gm_id=request.user.id, scenario_id=scenario.id, scenario_notes=None).all()
        games_run_no_feedback = [x for x in games_run_no_feedback if not x.is_scheduled() and not x.is_active()]
        if games_run_no_feedback:
            game_feedback = GameFeedbackForm()
        context = {
            'show_spoiler_warning': show_spoiler_warning,
            'scenario': scenario,
            'games_run': games_run,
            'games_run_no_feedback': games_run_no_feedback,
            'game_feedback_form': game_feedback,
        }
        return render(request, 'games/view_scenario.html', context)

def view_scenario_gallery(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to view your Scenario Gallery")
    owned_scenarios = request.user.scenario_creator.all()
    discovered_scenarios = request.user.scenario_discovery_set.exclude(reason=DISCOVERY_REASON[1][0]).all()
    num_new_cell_scenarios = len(Scenario.objects.filter(tags__slug="newcell").all())
    not_cell_leader = len(request.user.cell_set.filter(creator=request.user).all()) == 0
    context = {
        'owned_scenarios': owned_scenarios,
        'scenario_discoveries': discovered_scenarios,
        'num_new_cell_scenarios': num_new_cell_scenarios,
        'not_cell_leader': not_cell_leader,
    }
    return render(request, 'games/view_scenario_gallery.html', context)

def create_game(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to create a Game")
    if request.method == 'POST':
        form = make_game_form(user=request.user, game_status=GAME_STATUS[0][0])(request.POST)
        if form.is_valid():
            start_time = form.cleaned_data['scheduled_start_time']
            if "timezone" in form.cleaned_data:
                account = request.user.account
                account.timezone = form.cleaned_data["timezone"]
                account.save()
                start_time = change_time_to_current_timezone(start_time)
            game = Game(
                title = form.cleaned_data['title'],
                creator = request.user,
                gm = request.user,
                required_character_status = form.cleaned_data['required_character_status'],
                hook = form.cleaned_data['hook'],
                created_date = timezone.now(),
                scheduled_start_time = start_time,
                open_invitations = form.cleaned_data['open_invitations'],
                status = GAME_STATUS[0][0],
                cell = form.cleaned_data['cell']
            )
            if form.cleaned_data['scenario']:
                game.scenario = form.cleaned_data['scenario']
            with transaction.atomic():
                game.save()
                if form.cleaned_data['invite_all_members']:
                    for member in game.cell.cellmembership_set.exclude(member_player = game.gm):
                        game_invite = Game_Invite(invited_player=member.member_player,
                                                  relevant_game=game,
                                                  invite_text=game.hook,
                                                  as_ringer=False)
                        if member.member_player.has_perm("view_scenario", game.scenario):
                            game_invite.as_ringer = True
                        game_invite.save()
                        game_invite.notify_invitee(request, game)
            game_url = reverse('games:games_view_game', args=(game.id,))
            messages.add_message(request, messages.SUCCESS, mark_safe("Your Game has been created Successfully."
                                                                      "<br>"
                                                                      "<a href='"
                                                                      + game_url +
                                                                      "'> Click Here</a> "
                                                                      "if you do not want to invite anyone else at this time."))
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
    initial_data = {'title': game.title,
     'hook': game.hook,
     'scenario': game.scenario,
     'required_character_status': game.required_character_status,
     'start_time': convert_to_localtime(game.scheduled_start_time),
     'cell': game.cell,
     'open_invitations': game.open_invitations,
     }
    GameForm = make_game_form(user=request.user, game_status=game.status)
    if request.method == 'POST':
        if not request.user.has_perm('edit_game', game):
            raise PermissionDenied("You don't have permission to edit this Game event")
        form = GameForm(request.POST, initial=initial_data)
        if form.is_valid():
            game.title=form.cleaned_data['title']
            game.hook=form.cleaned_data['hook']
            start_time = form.cleaned_data['scheduled_start_time']
            if "timezone" in form.cleaned_data:
                account = request.user.account
                account.timezone = form.cleaned_data["timezone"]
                account.save()
                start_time = change_time_to_current_timezone(start_time)
            if game.is_scheduled():
                game.open_invitations = form.cleaned_data['open_invitations']
                game.scheduled_start_time = start_time
                game.required_character_status = form.cleaned_data['required_character_status']
                game.scenario=form.cleaned_data['scenario']
                game.cell = form.cleaned_data['cell']
                if form.cleaned_data['scenario']:
                    game.scenario = form.cleaned_data['scenario']
            with transaction.atomic():
                game.save()
                if game.is_scheduled() and hasattr(form.changed_data, 'invite_all_members') and form.cleaned_data['invite_all_members']:
                    for member in game.cell.cellmembership_set.exclude(member_player=game.gm):
                        game_invite = Game_Invite(invited_player=member.member_player,
                                                  relevant_game=game,
                                                  invite_text=game.hook,
                                                  as_ringer=False)
                        game_invite.save()
                        game_invite.notify_invitee(request, game)
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a game form.
        form = GameForm(initial=initial_data)
        context = {
            'game': game,
            'form' : form,
        }
        return render(request, 'games/edit_game.html', context)

def view_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    can_view_scenario = False
    my_invitation = None
    if request.user.is_authenticated:
        my_invitation = get_object_or_none(request.user.game_invite_set.filter(relevant_game=game_id))
    if request.user.has_perm("view_scenario", game.scenario):
        can_view_scenario = True
    invite_form = None
    if request.user.has_perm('edit_game', game) and game.is_scheduled():
        initial_data = {"message": game.hook}
        invite_form = CustomInviteForm(initial=initial_data)
    can_edit = request.user.is_authenticated and request.user.has_perm('edit_game', game)
    context = {
        'game': game,
        'can_view_scenario': can_view_scenario,
        'my_invitation': my_invitation,
        'invite_form': invite_form,
        'can_edit': can_edit,
    }
    return render(request, 'games/view_game_pages/view_game.html', context)

#TODO: if game is active, add option to share scenario with participants
def cancel_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        if not request.user.has_perm('edit_game', game):
            raise PermissionDenied("You don't have permission to edit this Game event")
        if not game.is_scheduled() and not game.is_active():
            raise PermissionDenied("You cannot cancel a game that has been completed")
        with transaction.atomic():
            game.transition_to_canceled()
        return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
    else:
        if not request.user.has_perm('edit_game', game):
            raise PermissionDenied("You don't have permission to edit this Game event")
        context = {
            'game': game,
        }
        return render(request, 'games/cancel_game.html', context)

def invite_players(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if not request.user.has_perm('edit_game', game) or not game.is_scheduled():
        raise PermissionDenied("You don't have permission to edit this Game event, or it has already started")
    initial_data = {"message": game.hook}
    if request.method == 'POST':
        form = CustomInviteForm(request.POST, initial=initial_data)
        if form.is_valid():
            player = get_object_or_404(User, username__iexact= form.cleaned_data['username'])
            if get_queryset_size(player.game_invite_set.filter(relevant_game=game)) > 0:
                #player is already invited. Maybe update invitation instead?
                raise PermissionDenied("Player already invited")
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
            print(form.errors)
            return None
    else:
        return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))

def accept_invite(request, game_id):
    if not request.user.is_authenticated or request.user.is_anonymous:
        raise PermissionDenied("You must log in to accept this Game invite")
    game = get_object_or_404(Game, id=game_id)
    if not game.is_scheduled() or game.creator.id == request.user.id or game.gm.id == request.user.id:
        raise PermissionDenied("This Game has already started, or you're the GM!")
    invite = get_object_or_none(request.user.game_invite_set.filter(relevant_game=game))
    if not invite and not game.open_invitations:
        raise PermissionDenied("This is awkward. . . You, uh, haven't been invited to this Game")
    if request.method == 'POST':
        if not invite:
            # player self-invite
            invite = Game_Invite(invited_player=request.user,
                                 relevant_game=game)
            if game.scenario in request.user.scenario_set.all():
                invite.as_ringer = True
        form =  make_accept_invite_form(invite)(request.POST)
        if form.is_valid():
            game_attendance = invite.attendance
            with transaction.atomic():
                invite.save()
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
                    if invite.as_ringer and not form.cleaned_data['attending_character']:
                        #Reveal scenario to ringer
                        game.scenario.played_discovery(request.user)
            return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))
        else:
            print(form.errors)
            return None
    else:
        can_view_scenario = False
        if request.user.has_perm("view_scenario", game.scenario):
            can_view_scenario = True
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
            'can_view_scenario': can_view_scenario,
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
            with transaction.atomic():
                invite.save()
    return HttpResponseRedirect(reverse('games:games_view_game', args=(game.id,)))

#TODO: Pull some of this into helper functions
#TODO: Enforce or advise on number of players constraints
def start_game(request, game_id, char_error=" ", player_error=" "):
    game = get_object_or_404(Game, id=game_id)
    if not request.user.has_perm('edit_game', game):
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
        raise PermissionDenied("You don't have permission to edi this Game Event")
    if not game.is_active():
        raise PermissionDenied("You can't end a Game event that isn't in progress")
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
            with transaction.atomic():
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
        raise PermissionDenied("You must be logged in to allocate improvements")
    avail_improvements = request.user.profile.get_avail_improvements()
    if len(avail_improvements) > 0:
        return HttpResponseRedirect(reverse('games:games_allocate_improvement', args=(avail_improvements.first().id,)))
    else:
        return HttpResponseRedirect(reverse('hgapp:home', args=()))

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
def create_ex_game_for_cell(request, cell_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must log in to create archival Game events")
    cell = get_object_or_404(Cell, id = cell_id)
    if not cell.player_can_manage_games(request.user):
        raise PermissionDenied("You do not have permission to manage Game Events for this Cell")
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
            #TODO: better error handling.
            raise ValueError("Player filled out the form wrong")
    else:
        context = get_context_for_choose_attending(cell)
        return render(request, 'games/create_ex_game_choose_attendance.html', context)

def finalize_create_ex_game_for_cell(request, cell_id, gm_user_id, players):
    if not request.user.is_authenticated:
        raise PermissionDenied("Log in, yo")
    cell = get_object_or_404(Cell, id = cell_id)
    if not cell.player_can_manage_games(request.user):
        raise PermissionDenied("You do not have permission to manage Game Events for this Cell")
    gm = get_object_or_404(User, id=gm_user_id)
    player_list = [get_object_or_404(User, id=player_id) for player_id in players.split('+') if not player_id == str(gm.id)]
    GenInfoForm = make_archive_game_general_info_form(gm)
    ArchivalOutcomeFormSet = formset_factory(ArchivalOutcomeForm, extra=0)
    if request.method == 'POST':
        general_form = GenInfoForm(request.POST, prefix="general")
        outcome_formset = ArchivalOutcomeFormSet(request.POST, prefix="outcome", initial=[{'player_id': x.id,
                                                           'invited_player': x}
                                                          for x in player_list])
        if general_form.is_valid() and outcome_formset.is_valid():
            create_archival_game(request, general_form, cell, outcome_formset)
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(cell.id,)))
        else:
            print(general_form.errors)
            print(outcome_formset.errors)
            raise ValueError("Invalid game form")
    else:
        context = get_context_for_create_finished_game(player_list, players, gm, cell, GenInfoForm, ArchivalOutcomeFormSet)
        return render(request, 'games/edit_archive_game.html', context)


# Choose additional players to add to a completed game.
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
            raise ValueError("Player filled out the form wrong")
    else:
        context = get_context_for_choose_attending(cell, game)
        return render(request, 'games/create_ex_game_choose_attendance.html', context)



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
    if not request.user.is_authenticated:
        raise PermissionDenied("You must log in.")
    if not (game.is_finished() or game.is_archived() or game.is_recorded()):
        raise PermissionDenied("You can't add an attendance to a Game that isn't finished.")
    if game.cell.player_can_manage_games(request.user):
        return
    if not request.user.has_perm('edit_game', game):
        raise PermissionDenied("You don't have permission to edit this Game")

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
                else:
                    invite = attendance.game_invite
                    invite.is_declined = True
                    invite.save()
        else:
            print(form.errors)
        return HttpResponseRedirect(reverse('games:games_view_game', args=(attendance.relevant_game.id,)))
    else:
        return render_confirm_attendance_page(request, attendance)

def render_confirm_attendance_page(request, attendance):
    form = RsvpAttendanceForm()
    context = {
        'form': form,
        'attendance': attendance,
    }
    return render(request, 'games/confirm_attendance.html', context)

def spoil_scenario(request, scenario_id):
    if not request.user.is_authenticated:
        return JsonResponse({}, status=200)
    else:
        if request.is_ajax and request.method == "POST":
            scenario = get_object_or_404(Scenario, id=scenario_id)
            with transaction.atomic():
                if not scenario.player_discovered(request.user):
                    scenario.unlocked_discovery(request.user)
            return JsonResponse({}, status=200)
        return JsonResponse({"error": ""}, status=400)