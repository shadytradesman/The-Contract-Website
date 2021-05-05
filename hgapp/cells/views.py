from django.contrib.auth.models import User
from django.views import View
from django.shortcuts import render
from django.db import transaction
from cells.forms import EditCellForm, CustomInviteForm, RsvpForm, PlayerRoleForm, KickForm, EditWorldForm
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.safestring import mark_safe

from hgapp.utilities import get_object_or_none
from .models import Cell, ROLE, CellInvite
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from games.models import Scenario
from games.games_constants import GAME_STATUS
from django.core.exceptions import PermissionDenied
from postman.api import pm_write
from django.utils.safestring import SafeText
from django.forms import formset_factory

def create_cell(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to create a cell")
    if not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    if request.method == 'POST':
        form = EditCellForm(request.POST)
        if form.is_valid():
            cell = Cell(
                name = form.cleaned_data['name'],
                creator = request.user,
                setting_name = form.cleaned_data['setting_name'],
                setting_description = form.cleaned_data['setting_description'],
            )
            new_cell_scenarios = Scenario.objects.filter(tags__slug="newcell").all()
            with transaction.atomic():
                cell.save()
                for scenario in new_cell_scenarios:
                    scenario.unlocked_discovery(request.user)
            if len(request.user.cell_set.filter(creator=request.user).all()) == 1:
                gallery_url = reverse('games:games_view_scenario_gallery')
                num_unlocked = len(new_cell_scenarios)
                messages.add_message(request, messages.SUCCESS, mark_safe("<h4 class=\"text-center\">By creating this Cell "
                                                                          "you have unlocked <b>" + str(num_unlocked) + "</b> premade stock Scenarios!"
                                                                          "<br>"
                                                                          "<a href='"
                                                                          + gallery_url +
                                                                          "'> Click Here</a> "
                                                                          "to visit your Scenario Gallery</h4>"))
            return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(cell.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a Cell form
        form = EditCellForm()
        context = {
            'form' : form,
        }
        return render(request, 'cells/edit_cell.html', context)

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class EditWorld(View):
    form_class = EditWorldForm
    template_name = 'cells/edit.html'
    initial = {}
    cell = None
    INITIAL_DATA_CELL_ID = 1

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

#
# @method_decorator(login_required(login_url='account_login'), name='dispatch')
# class EditWorld(View):
#     form_class = EditWorldForm
#     template_name = 'cells/edit.html'
#     initial = {}
#     cell = None
#
#     def dispatch(self, *args, **kwargs):
#         self.cell = get_object_or_404(Cell, id=self.kwargs['cell_id'])
#         self.__check_permissions()
#         self.initial = {
#             "name": self.cell.name,
#             "setting_sheet_blurb": self.cell.setting_sheet_blurb,
#             "setting_description": self.cell.setting_description,
#             "setting_summary": self.cell.setting_summary,
#             "setting_create_char_info": self.cell.setting_create_char_info,
#             "are_contractors_portable": self.cell.are_contractors_portable,
#             "house_rules": self.cell.house_rules,
#         }
#         return super().dispatch(*args, **kwargs)
#
#     def get(self, request, *args, **kwargs):
#         return render(request, self.template_name, self.__get_context_data())
#
#     def post(self, request, *args, **kwargs):
#         form = self.form_class(request.POST)
#         if form.is_valid():
#             new_cell_scenarios = Scenario.objects.filter(tags__slug="newcell").all()
#             with transaction.atomic():
#                 self.cell.name = form.cleaned_data['name']
#                 self.cell.setting_name = form.cleaned_data['name']
#                 self.cell.setting_sheet_blurb = form.cleaned_data['setting_sheet_blurb']
#                 self.cell.setting_description = form.cleaned_data['setting_description']
#                 self.cell.setting_summary = form.cleaned_data['setting_summary']
#                 self.cell.setting_create_char_info = form.cleaned_data['setting_create_char_info']
#                 self.cell.house_rules = form.cleaned_data['house_rules']
#                 self.cell.are_contractors_portable = form.cleaned_data['are_contractors_portable']
#                 self.cell.save()
#                 if request.user == self.cell.creator:
#                     for scenario in new_cell_scenarios:
#                         scenario.unlocked_discovery(request.user)
#             return HttpResponseRedirect(reverse('cells:cells_view_cell', args=(self.cell.id,)))
#         raise ValueError("Invalid edit setting form")
#
#     def __check_permissions(self):
#         if not self.cell.player_can_edit_world(self.request.user):
#             raise PermissionDenied("You don't have permissions to edit this Cell's setting.")
#
#     def __get_context_data(self):
#         context = {
#             'cell': self.cell,
#             'form': self.form_class(initial=self.initial),
#         }
#         return context
#

def view_cell(request, cell_id):
    cell = get_object_or_404(Cell, id=cell_id)
    #TODO: View permissions? Private cells?
    can_manage_memberships = cell.player_can_manage_memberships(request.user)
    can_edit_world = cell.player_can_edit_world(request.user)
    user_membership = None
    invite = None
    if request.user.is_authenticated:
        invite = get_object_or_none(cell.open_invitations().filter(invited_player=request.user))
        user_membership = cell.get_player_membership(request.user)
        if not request.user.profile.confirmed_agreements:
            return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    can_edit_characters = cell.player_can_edit_characters(request.user)
    can_administer = cell.player_can_admin(request.user)
    can_manage_games = cell.player_can_manage_games(request.user)
    memberships_and_characters = ()
    for role in ROLE:
        for membership in cell.cellmembership_set.filter(role = role[0]):
            characters = ()
            for character in membership.member_player.character_set.filter(cell = cell, is_deleted=False):
                if not character.is_dead():
                    characters = characters + (character,)
            memberships_and_characters = memberships_and_characters + ((membership, characters,),)
    upcoming_games = cell.game_set.filter(status = GAME_STATUS[0][0])
    completed_games = cell.completed_games()

    context = {
        'cell': cell,
        'can_edit_world': can_edit_world,
        'can_manage_memberships': can_manage_memberships,
        'can_edit_characters': can_edit_characters,
        'user_membership': user_membership,
        'can_administer': can_administer,
        'can_manage_games': can_manage_games,
        'memberships_and_characters': memberships_and_characters,
        'upcoming_games': upcoming_games,
        'completed_games': completed_games,
        'invite': invite,
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
        if not secret_key or not cell.invite_link_secret_key == secret_key:
            raise PermissionDenied("This Cell invite link has expired. Ask for a new one.")
    if request.method == 'POST':
        form = RsvpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if is_accepted and invite:
                    invite.accept()
                elif is_accepted and cell.invite_link_secret_key == secret_key:
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
    FormSet = formset_factory(PlayerRoleForm, extra=0)
    if request.method == 'POST':
        membership_formset = FormSet(request.POST)
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
        membership_formset = FormSet(initial=[{'player_id': x.member_player.id,
                                               'role': x.role,
                                               'username': x.member_player,
                                               'role_display': x.get_role_display()} for x in cell_members])
        kick_form = KickForm()
        context = {
            'formset': membership_formset,
            'kick_form': kick_form,
            'cell': cell,
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
