from django.contrib.auth.models import User
from django.views import View
from django.shortcuts import render
from django.db import transaction
from cells.forms import CustomInviteForm, RsvpForm, PlayerRoleForm, KickForm, EditWorldForm, EditWorldEventForm, \
    RecruitmentForm, RolePermissionForm
from cells.models import CELL_PERMISSIONS
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.safestring import mark_safe
from collections import defaultdict

from hgapp.utilities import get_object_or_none
from .models import Cell, ROLE, CellInvite, WorldEvent, CellMembership
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from games.models import Scenario
from games.games_constants import GAME_STATUS
from journals.models import Journal
from django.core.exceptions import PermissionDenied
from postman.api import pm_write
from django.utils.safestring import SafeText
from django.forms import formset_factory


@method_decorator(login_required(login_url='account_login'), name='dispatch')
class EditWorld(View):
    form_class = EditWorldForm
    template_name = 'cells/edit.html'
    initial = {}
    cell = None
    INITIAL_DATA_CELL_ID = 2

    def dispatch(self, *args, **kwargs):
        if 'cell_id' in self.kwargs:
            self.cell = get_object_or_404(Cell, id=self.kwargs['cell_id'])
            initial_data_cell = self.cell
        else:
            initial_data_cell = get_object_or_404(Cell, id=self.INITIAL_DATA_CELL_ID)
        self.__check_permissions()
        self.initial = {
            "name": initial_data_cell.name,
            "setting_sheet_blurb": initial_data_cell.setting_sheet_blurb,
            "setting_description": initial_data_cell.setting_description,
            "setting_summary": initial_data_cell.setting_summary,
            "setting_create_char_info": initial_data_cell.setting_create_char_info,
            "are_contractors_portable": initial_data_cell.are_contractors_portable,
            "house_rules": initial_data_cell.house_rules,
        }
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            new_cell = not self.cell
            if new_cell:
                self.cell = Cell(creator=request.user)
            self.cell.name = form.cleaned_data['name']
            self.cell.setting_name = form.cleaned_data['name']
            self.cell.setting_sheet_blurb = form.cleaned_data['setting_sheet_blurb']
            self.cell.setting_description = form.cleaned_data['setting_description']
            self.cell.setting_summary = form.cleaned_data['setting_summary']
            self.cell.setting_create_char_info = form.cleaned_data['setting_create_char_info']
            self.cell.house_rules = form.cleaned_data['house_rules']
            self.cell.are_contractors_portable = form.cleaned_data['are_contractors_portable']
            with transaction.atomic():
                self.cell.save()
                if new_cell:
                    self.__unlock_scenarios()
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(self.cell.id,)))
        raise ValueError("Invalid edit setting form")

    def __unlock_scenarios(self):
        # re-unlock the scenarios even if it isn't their first cell since more may be added later.
        new_cell_scenarios = Scenario.objects.filter(tags__slug="newcell").all()
        for scenario in new_cell_scenarios:
            scenario.unlocked_discovery(self.request.user)
        if len(self.request.user.cell_set.filter(creator=self.request.user).all()) == 1:
            gallery_url = reverse('games:games_view_scenario_gallery')
            num_unlocked = len(new_cell_scenarios)
            messages.add_message(self.request, messages.SUCCESS, mark_safe("<h4 class=\"text-center\">By creating this Cell "
                                                                      "you have unlocked <b>" + str(num_unlocked)
                                                                      + "</b> premade stock Scenarios!" 
                                                                        "<br>"
                                                                        "<a href='" + gallery_url + "'> Click Here</a> "
                                                                      "to visit your Scenario Gallery</h4>"))

    def __check_permissions(self):
        if self.cell:
            if not self.cell.player_can_edit_world(self.request.user):
                raise PermissionDenied("You don't have permissions to edit this Cell's setting.")

    def __get_context_data(self):
        context = {
            'cell': self.cell,
            'form': self.form_class(initial=self.initial),
        }
        return context


@method_decorator(login_required(login_url='account_login'), name='dispatch')
class EditFindWorld(View):
    form_class = RecruitmentForm
    template_name = 'cells/edit_find_world.html'
    initial = {}
    cell = None

    def dispatch(self, *args, **kwargs):
        self.cell = get_object_or_404(Cell, id=self.kwargs['cell_id'])
        self.__check_permissions()
        self.initial = {
            "list_publicly": self.cell.is_listed_publicly,
            "allow_self_invites": self.cell.allow_self_invites,
            "cell_sell": self.cell.cell_sell,
            "community_link": self.cell.community_link,
            "is_community_link_public": self.cell.is_community_link_public,
        }
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            self.cell.is_listed_publicly = form.cleaned_data['list_publicly']
            self.cell.allow_self_invites = form.cleaned_data['allow_self_invites']
            self.cell.cell_sell = form.cleaned_data['cell_sell']
            self.cell.community_link = form.cleaned_data['community_link']
            self.cell.is_community_link_public = form.cleaned_data["is_community_link_public"]
            with transaction.atomic():
                self.cell.save()
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(self.cell.id,)))
        raise ValueError("Invalid edit setting form")

    def __check_permissions(self):
        if not self.cell.player_can_manage_memberships(self.request.user):
            raise PermissionDenied("You don't have permissions to edit the recruitment materials.")

    def __get_context_data(self):
        context = {
            'cell': self.cell,
            'form': self.form_class(initial=self.initial),
        }
        return context

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class PostWorldEvent(View):
    form_class = EditWorldEventForm
    template_name = 'cells/post_world_event.html'
    initial = {}
    cell = None
    world_event = None

    def dispatch(self, *args, **kwargs):
        self.cell = get_object_or_404(Cell, id=self.kwargs['cell_id'])
        if "world_event_id" in self.kwargs:
            self.world_event = get_object_or_404(WorldEvent, id=self.kwargs['world_event_id'])
            self.initial = {
                "headline": self.world_event.headline,
                "event_description": self.world_event.event_description,
            }
        self.__check_permissions()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            posting_new_event = not self.world_event
            if posting_new_event:
                self.world_event = WorldEvent(creator=request.user,
                                              parent_cell=self.cell,)
            else:
                if form.cleaned_data["should_delete"]:
                    with transaction.atomic():
                        self.world_event.delete()
                    return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(self.cell.id,)))
            self.world_event.headline = form.cleaned_data["headline"] if "headline" in form.cleaned_data else " "
            self.world_event.event_description = form.cleaned_data["event_description"]
            with transaction.atomic():
                self.world_event.save()
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(self.cell.id,)))
        raise ValueError("Invalid edit setting form")

    def __check_permissions(self):
        if not self.world_event:
            if not self.cell.player_can_post_world_events(self.request.user):
                raise PermissionDenied("You don't have permission to post World Events here.")
        else:
            if not self.cell.player_can_edit_world(self.request.user) and not self.world_event.creator == self.request.user:
                raise PermissionDenied("You don't have permission to edit this World Event.")


    def __get_context_data(self):
        context = {
            'cell': self.cell,
            'form': self.form_class(initial=self.initial),
            'world_event': self.world_event,
        }
        return context


def view_cell(request, cell_id):
    cell = get_object_or_404(Cell, id=cell_id)
    user_membership = None
    invite = None
    can_manage_memberships = None
    can_edit_world = None
    can_edit_characters = None
    can_administer = None
    can_manage_games = None
    can_post_world_events = None
    can_gm = None
    my_cell_contractors = None
    if request.user.is_authenticated:
        if not request.user.profile.confirmed_agreements:
            return HttpResponseRedirect(reverse('profiles:profiles_terms'))
        invite = get_object_or_none(cell.open_invitations().filter(invited_player=request.user))
        user_membership = cell.get_player_membership(request.user)
        can_manage_memberships = cell.player_can_manage_memberships(request.user)
        can_edit_world = cell.player_can_edit_world(request.user)
        can_edit_characters = cell.player_can_edit_characters(request.user)
        can_administer = cell.player_can_admin(request.user)
        can_manage_games = cell.player_can_manage_games(request.user)
        can_post_world_events = cell.player_can_post_world_events(request.user)
        can_gm = cell.player_can_run_games(request.user)
        my_cell_contractors = request.user.character_set.filter(cell=cell, is_deleted=False)

    memberships_and_characters = ()
    for role in ROLE:
        for membership in cell.cellmembership_set.filter(role = role[0]):
            characters = ()
            for character in membership.member_player.character_set.filter(cell=cell, is_deleted=False):
                if not character.is_dead():
                    characters = characters + (character,)
            memberships_and_characters = memberships_and_characters + ((membership, characters,),)
    upcoming_games = cell.game_set.filter(status = GAME_STATUS[0][0])
    completed_games = cell.completed_games()
    world_events = WorldEvent.objects.filter(parent_cell=cell).order_by("-created_date").all()

    can_view_community_link = cell.is_community_link_public or user_membership
    community_link = cell.community_link if can_view_community_link else None

    journal_query = Journal.objects.filter(game_attendance__attending_character__private=False)\
        .filter(game_attendance__relevant_game__cell=cell)
    if request.user.is_anonymous:
        journal_query.filter(contains_spoilers=False, is_nsfw=False)
    elif not request.user.profile.view_adult_content:
        journal_query.filter(is_nsfw=False)
    public_journals = journal_query.order_by('-created_date').all()[:20]
    max_journals_to_display = 20
    displayed_journals = []
    for journal in public_journals:
        if max_journals_to_display <= len(displayed_journals):
            break
        if journal.player_can_view(request.user):
            displayed_journals.append(journal)

    context = {
        'cell': cell,
        'can_edit_world': can_edit_world,
        'can_manage_memberships': can_manage_memberships,
        'can_edit_characters': can_edit_characters,
        'user_membership': user_membership,
        'can_administer': can_administer,
        'can_manage_games': can_manage_games,
        'can_post_world_events': can_post_world_events,
        'can_gm': can_gm,
        'memberships_and_characters': memberships_and_characters,
        'upcoming_games': upcoming_games,
        'completed_games': completed_games,
        'invite': invite,
        'my_cell_contractors': my_cell_contractors,
        'world_events': world_events,
        'community_link': community_link,
        'latest_journals': displayed_journals,
    }
    return render(request, 'cells/view_cell.html', context)

def invite_players(request, cell_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to invite players to a Cell")
    cell = get_object_or_404(Cell, id=cell_id)
    # check "manage memberships" permissions
    if not cell.player_can_manage_memberships(request.user):
        raise PermissionDenied("You don't have permissions to manage memberships for this Cell")
    if request.method == 'POST':
        form = CustomInviteForm(request.POST)
        if form.is_valid():
            player = get_object_or_404(User, username__iexact=form.cleaned_data['username'])
            with transaction.atomic():
                cell.invitePlayer(player, form.cleaned_data['invite_text'])
            message_body = SafeText('###{0} has invited you to join [{1}]({2}).\n [Click Here]({3}) to respond.'
                                    .format(request.user.get_username(),
                                            cell.name,
                                            request.build_absolute_uri(reverse("cells:cells_view_cell", args=[cell.id])),
                                            request.build_absolute_uri(reverse("cells:cells_rsvp_invite", args=[cell.id])),
                                            ))
            with transaction.atomic():
                pm_write(sender=request.user,
                         recipient=player,
                         subject="You have been invited to join a Cell",
                         body=message_body,
                         skip_notification=False,
                         auto_archive=True,
                         auto_delete=False,
                         auto_moderators=None)
            return HttpResponseRedirect(reverse('cells:cells_invite_players', args=(cell.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build an invite form
        form = CustomInviteForm(auto_id=False)
        context = {
            'form': form,
            'cell': cell,
        }
        return render(request, 'cells/invite_players.html', context)


def rsvp_invite(request, cell_id, secret_key = None, accept = None):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to RSVP to a Cell invitation")
    if accept:
        is_accepted = accept == 'y'
    else:
        is_accepted = False
    cell = get_object_or_404(Cell, id=cell_id)
    if cell.get_player_membership(request.user):
        return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(cell.id,)))
    invite = get_object_or_none(cell.open_invitations().filter(invited_player=request.user))
    if not invite:
        if not cell.allow_self_invites and (not secret_key or not cell.invite_link_secret_key == secret_key):
            raise PermissionDenied("You have not been invited to this World or your invite link has expired. Ask for a new one.")
    if request.method == 'POST':
        form = RsvpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if is_accepted and invite:
                    invite.accept()
                elif is_accepted and not invite:
                    cell.addPlayer(request.user, ROLE[2])
                elif invite:
                    invite.reject()
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(cell.id,)))
        else:
            print(form.errors)
            return None
    else:
        form = RsvpForm()
        context = {
            'form': form,
            'cell': cell,
            'secret_key': secret_key,
        }
        return render(request, 'cells/rsvp_invite.html', context)


#TODO: use a form like in rsvp_invite to prevent cross site scripting attacks
def reset_invite_link(request, cell_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to reset the invite link")
    cell = get_object_or_404(Cell, id=cell_id)
    # check "manage memberships" permissions
    if not cell.player_can_manage_memberships(request.user):
        raise PermissionDenied("You don't have permission to manage the memberships of this Cell")
    with transaction.atomic():
        cell.resetShareLink()
    return HttpResponseRedirect(reverse("cells:cells_invite_players", args=(cell.id,)))

def revoke_invite(request, cell_id, invite_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to revoke a Cell invitation")
    cell = get_object_or_404(Cell, id=cell_id)
    if not cell.player_can_manage_memberships(request.user):
        raise PermissionDenied("You don't have permission to manage the memberships of this Cell")
    invite = get_object_or_404(CellInvite, id=invite_id)
    with transaction.atomic():
        invite.reject()
    return HttpResponseRedirect(reverse("cells:cells_invite_players", args=(cell.id,)))

def leave_cell(request, cell_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to leave a Cell")
    cell = get_object_or_404(Cell, id=cell_id)
    if not cell.get_player_membership(request.user):
        raise PermissionDenied("You can't leave a Cell you're not a member of")
    if request.method == 'POST':
        form = RsvpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                cell.removePlayer(request.user)
            return HttpResponseRedirect("/")
        else:
            print(form.errors)
            return None
    else:
        form = RsvpForm()
        context = {
            'form': form,
            'cell': cell,
        }
        return render(request, 'cells/leave_cell.html', context)

def manage_members(request, cell_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to revoke a Cell invitation")
    cell = get_object_or_404(Cell, id=cell_id)
    if not cell.player_can_manage_memberships(request.user):
        raise PermissionDenied("You don't have permission to manage the memberships of this Cell")
    cell_members = cell.cellmembership_set.order_by("role").all()
    MemberFormSet = formset_factory(PlayerRoleForm, extra=0)
    if request.method == 'POST':
        membership_formset = MemberFormSet(request.POST)
        if membership_formset.is_valid():
            with transaction.atomic():
                for form in membership_formset:
                    player = get_object_or_404(User, id=int(form.cleaned_data['player_id']))
                    membership = cell.cellmembership_set.get(member_player=player)
                    form_role = form.cleaned_data['role']
                    if membership.role != form_role:
                        if (membership.role == ROLE[0][0] or form_role == ROLE[0][0])\
                                and not cell.player_can_admin(request.user):
                            raise PermissionDenied("Coup averted: You must be a Cell leader to promote a Cell leader")
                        membership.role = form.cleaned_data['role']
                        membership.save()
            return HttpResponseRedirect(reverse('cells:cells_manage_members', args=(cell.id,)))
        else:
            print(membership_formset.errors)
            return None
    else:
        membership_formset = MemberFormSet(initial=[{'player_id': x.member_player.id,
                                               'role': x.role,
                                               'username': x.member_player,
                                               'role_display': x.get_role_display()} for x in cell_members])
        kick_form = KickForm()
        perms_by_role = defaultdict(list)
        for role in ROLE:
            for x in cell.get_permissions_for_role(role[0]).enabled_permissions():
                perms_by_role[role[1]].append(x[1])
        can_edit_perms = cell.player_can_admin(request.user)
        context = {
            'formset': membership_formset,
            'kick_form': kick_form,
            'cell': cell,
            'perms_by_role': dict(perms_by_role),
            'can_edit_perms': can_edit_perms,
        }
        return render(request, 'cells/manage_members.html', context)

def kick_player(request, cell_id, user_id):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to manage your Cell")
    cell = get_object_or_404(Cell, id=cell_id)
    player = get_object_or_404(User, id=int(user_id))
    if not cell.player_can_manage_memberships(request.user):
        raise PermissionDenied("You don't have permission to manage the memberships of this Cell")
    if request.method == 'POST':
        form = KickForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                cell.removePlayer(player)
        else:
            print(form.errors)
        return HttpResponseRedirect(reverse('cells:cells_manage_members', args=(cell.id,)))
    else:
        return HttpResponseRedirect(reverse('cells:cells_manage_members', args=(cell.id,)))


class FindWorld(View):
    template_name = 'cells/find_world.html'

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __get_context_data(self):
        public_cells = Cell.objects.filter(is_listed_publicly=True).order_by('-find_world_date').all()
        context = {
            'public_cells': public_cells,
        }
        return context

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class ManageRoles(View):
    form_class = RolePermissionForm
    template_name = 'cells/edit_roles.html'
    initial = {}
    cell = None
    INITIAL_DATA_CELL_ID = 1

    def dispatch(self, *args, **kwargs):
        self.cell = get_object_or_404(Cell, id=self.kwargs['cell_id'])
        self.__check_permissions()
        self.initial = []
        for role in ROLE[1:]:
            perms = self.cell.get_permissions_for_role(role[0])
            self.initial.append({
                'role_display': role[1],
                'role': role[0],
                'can_manage_memberships': perms.can_manage_memberships,
                'can_gm_games': perms.can_manage_roles,
                'can_post_events': perms.can_post_events,
                'can_manage_member_characters': perms.can_manage_member_characters,
                'can_edit_world': perms.can_edit_world,
                'can_manage_games': perms.can_manage_games,
            })
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        RolePermissionFormSet = formset_factory(self.form_class, extra=0)
        formset = RolePermissionFormSet(request.POST)
        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    if form.cleaned_data['role'] == ROLE[0][0]:
                        raise ValueError("cannot edit administrator permissions")
                    perms = self.cell.get_permissions_for_role(form.cleaned_data['role'])
                    if not perms:
                        raise ValueError("Cannot find perms for role")
                    perms.can_manage_memberships = form.cleaned_data['can_manage_memberships']
                    perms.can_manage_roles = form.cleaned_data['can_gm_games']
                    perms.can_post_events = form.cleaned_data['can_post_events']
                    perms.can_manage_member_characters = form.cleaned_data['can_manage_member_characters']
                    perms.can_edit_world = form.cleaned_data['can_edit_world']
                    perms.can_manage_games = form.cleaned_data['can_manage_games']
                    perms.save()
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(self.cell.id,)))
        raise ValueError("Invalid role permissions form.")

    def __check_permissions(self):
        if self.cell:
            if not self.cell.player_can_admin(self.request.user):
                raise PermissionDenied("You don't have permissions to edit this World's roles.")

    def __get_context_data(self):
        RolePermissionFormSet = formset_factory(self.form_class, extra=0)
        formset = RolePermissionFormSet(initial=self.initial)
        context = {
            'cell': self.cell,
            'formset': formset,
            'permissions': CELL_PERMISSIONS[1:],
        }
        return context
