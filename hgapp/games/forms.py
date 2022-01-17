from django import forms
from itertools import groupby
from django.forms.models import ModelChoiceField, ModelChoiceIterator
from itertools import chain

from characters.models import HIGH_ROLLER_STATUS, SEASONED_PORTED, VETERAN_PORTED
from django.forms import ModelChoiceField
from account.conf import settings
from django.utils import timezone
from django.db.models import Q

from games.models import OUTCOME, ScenarioTag, REQUIRED_HIGH_ROLLER_STATUS, INVITE_MODE, GameMedium
from .games_constants import EXP_V1_V2_GAME_ID
from characters.models import Character

from bootstrap3_datetime.widgets import DateTimePicker

from tinymce.widgets import TinyMCE

class ScenarioModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.choice_txt()

class CreateScenarioForm(forms.Form):
    title = forms.CharField(label='Title',
                           max_length=130,
                           help_text='This Scenario\'s title. This may be seen by people who have not played the Scenario.')
    summary = forms.CharField(label='Summary',
                              max_length=400,
                              required=False,
                              help_text="Summarize the Scenario so that people who have already played it can recognize it.")
    description = forms.CharField(label='Write-up',
                            widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                            max_length=70000,
                            help_text='Describe the Scenario in detail. Win conditions, enemies, background, etc.')
    max_players = forms.IntegerField(label = "Max Players", initial=4)
    min_players = forms.IntegerField(label = "Minimum Players", initial=2)
    suggested_character_status = forms.ChoiceField(label = "Required Status",
                                                   choices=HIGH_ROLLER_STATUS,
                                                   help_text='Must be this tall to ride')
    is_highlander = forms.BooleanField(label = "Highlander",
                                       required=False,
                                       help_text = "Only one Contractor can achieve victory")
    is_rivalry = forms.BooleanField(label = "Rivalry",
                                    required=False,
                                    help_text="The Contractors may have different or opposing goals")
    requires_ringer = forms.BooleanField(label = "Requires Ringer",
                                         required=False,
                                         help_text="One Player must play an NPC instead of their Contractor")
    tags = forms.ModelMultipleChoiceField(queryset=ScenarioTag.objects.order_by("tag").all(),
                                          required=False,
                                          widget=forms.CheckboxSelectMultiple)

class CustomInviteForm(forms.Form):
    username = forms.CharField(label='Player\'s Username',
                                max_length=200)
    message = forms.CharField(label='Message',
                               max_length=5000,
                               widget=forms.Textarea,
                               help_text='Personalize the invite for this Player',
                               required=False)
    invite_as_ringer = forms.BooleanField(label="Invite as Ringer",
                                          required=False,
                                          help_text="Invite this player to play an NPC. The Scenario will be revealed to them if they accept.")

def make_game_form(user):
    class CreateGameForm(forms.Form):
        date_format= '%m/%d/%Y %I:%M %p'
        title = forms.CharField(label='Scenario Name',
                               max_length=100,
                               help_text='The name for the newly-created Scenario.',
                               required=False)
        hook = forms.CharField(label='Invitation Text',
                               widget=forms.Textarea,
                               max_length=5000,
                               help_text='Entice Players and provide information.')
        timezone = forms.ChoiceField(
            label= ("My Timezone"),
            choices=settings.ACCOUNT_TIMEZONES,
            required=False,
            initial=user.account.timezone
        )
        all_cells = user.cell_set.all()
        cell_ids = {cell.id for cell in all_cells if cell.player_can_run_games(user)}
        queryset = user.cell_set.filter(id__in=cell_ids).all()
        scenario = ScenarioModelChoiceField(queryset=user.scenario_set.filter(scenario_discovery__is_spoiled=True).order_by("-num_words").all(),
                                          empty_label="Create New Scenario",
                                          required=False,
                                          help_text='Select the Scenario that the Contract will follow.')
        scheduled_start_time = forms.DateTimeField(widget=DateTimePicker(options=False),
                                                   input_formats=[date_format],
                                                   help_text='For planning purposes. Places no actual restrictions on starting the Contract.')
        cell = forms.ModelChoiceField(label="Playgroup",
                                      queryset=queryset,
                                      empty_label="Select a Playgroup",
                                      help_text="Select a Playgroup for this Contract. This generally defines the setting of "
                                                "the Contract, although some Scenarios may see the Contractors spirited away "
                                                "to other dimensions, pocket realms, or similar. "
                                                "Playgroup leaders have the power to edit or void Contracts "
                                                "run in their Playgroup.",
                                      required=True)

        invite_all_members = forms.BooleanField(initial=False,
                                                required=False,
                                                label='Invite all Playgroup Members',
                                                help_text="Automatically send an invite and notification to all members "
                                                          "of the chosen Playgroup. ")
        required_character_status = forms.ChoiceField(label="Required Contractor Status",
                                                      choices=REQUIRED_HIGH_ROLLER_STATUS,
                                                      help_text='Players will only be able to RSVP with Contractors of the selected Status.')
        if user.profile.view_adult_content:
            only_over_18 = forms.BooleanField(initial=False,
                                              required=False,
                                              label='Only allow 18+ Players',
                                              help_text="If selected, only Players over the age of 18 will be able"
                                                        " to attend. This does not imply anything about the content of "
                                                        " the Contract.", )

        invitation_mode = forms.ChoiceField(label="Who can RSVP?",
                                            choices=INVITE_MODE,
                                            initial=INVITE_MODE[2],
                                            help_text='Determine who is allowed to RSVP to this Contract. Specifically '
                                                      'invited Players may always RSVP unless the Contract is closed.')
        list_in_lfg = forms.BooleanField(initial=True,
                                         required=False,
                                         label='List on LFG',
                                         help_text="If checked, this Contract will appear on the Looking-For-Game page. Do "
                                                   "not list in-person Contracts on the LFG page.")
        max_rsvp = forms.IntegerField(label="Capacity",
                                      required=False,
                                      help_text="Optional. Specify a limit on how many Players can RSVP to this Contract.",
                                      widget=forms.NumberInput(attrs={'class': 'ability-value-input form-control'}))
        allow_ringers = forms.BooleanField(initial=True,
                                           required=False,
                                           label='Allow Ringers',
                                           help_text="If checked, Players will be able to RSVP as an NPC Ringer. (Note: "
                                                     "other Players cannot see who has RSVPed until after the Contract.)")
        gametime_url = forms.CharField(label='Communication URL',
                                       max_length=1500,
                                       help_text='Optional. A link to the location (video call, Discord server, Roll20 '
                                                 'room, etc.) where the Contract will take place. It is revealed to Players after '
                                                 'they are invited or RSVP.',
                                       required=False)
        mediums = forms.ModelMultipleChoiceField(queryset=GameMedium.objects.order_by("medium").all(),
                                                 required=False,
                                                 widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled list-inline'}),
                                                 help_text='How will the Players communicate during the Contract? Select all'
                                                           ' that apply.')

        def default_date(self):
            if self.initial and 'start_time' in self.initial:
                #if you pass this in with the same name as the field, you get initial value issues
                return self.initial['start_time'].strftime(self.date_format)
            return None

    return CreateGameForm

def buildContractorChoiceIterator(game_cell=None):
    class ContractorChoiceIterator(ModelChoiceIterator):
        def __len__(self):
            return self.queryset.count() + (1 if self.field.empty_label is not None else 0)

        def __iter__(self):
            if game_cell:
                in_cell_contractors = self.queryset.filter(cell=game_cell).select_related('cell').order_by('cell__name', 'name')
                out_cell_contractors = self.queryset.exclude(cell=game_cell).select_related('cell').order_by('cell__name', 'name')
                queryset = chain(in_cell_contractors, out_cell_contractors)
                groups = groupby(queryset, key=lambda x: x.cell == game_cell)
            else:
                queryset = self.queryset.select_related('cell').order_by('cell__name', 'name')
                groups = groupby(queryset, key=lambda x: x.cell)
            if self.field.empty_label is not None:
                yield ("", self.field.empty_label)
            for world, contractors in groups:
                yield [
                    "In-Playgroup" if game_cell and world else "Out-of-Playgroup" if game_cell else world.name if world else None,
                    [
                        (contractor.id, contractor.name)
                        for contractor in contractors
                    ]
                ]
    return ContractorChoiceIterator

class CharDisplayModelChoiceField(ModelChoiceField):
    def __init__(self, world=None, *args, **kwargs):
        self.iterator = buildContractorChoiceIterator(world)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, character):
        return "{} ({} Victories)".format(character.name, character.number_of_victories())


def make_accept_invite_form(invitation):
    class AcceptInviteForm(forms.Form):
        users_living_character_ids = [char.id for char in invitation.invited_player.character_set.filter(is_deleted=False).all() if not char.is_dead()]
        required_status = invitation.relevant_game.required_character_status
        if required_status == REQUIRED_HIGH_ROLLER_STATUS[0][0]: # any
            queryset = Character.objects.filter(id__in=users_living_character_ids)
        elif required_status == REQUIRED_HIGH_ROLLER_STATUS[1][0]: # newbie or novice
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(status__in=[HIGH_ROLLER_STATUS[1][0], HIGH_ROLLER_STATUS[2][0]])
        elif required_status == REQUIRED_HIGH_ROLLER_STATUS[2][0]:  # newbie only
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(status=HIGH_ROLLER_STATUS[1][0])
        elif required_status == REQUIRED_HIGH_ROLLER_STATUS[3][0]:  # novice only
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(status=HIGH_ROLLER_STATUS[2][0])
        elif required_status == REQUIRED_HIGH_ROLLER_STATUS[4][0]:  # seasoned only
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(Q(status=HIGH_ROLLER_STATUS[3][0]) | Q(ported=SEASONED_PORTED))
        elif required_status == REQUIRED_HIGH_ROLLER_STATUS[5][0]:  # veteran only
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(Q(status=HIGH_ROLLER_STATUS[4][0]) | Q(ported=VETERAN_PORTED))
        else:
            raise ValueError("unanticipated required roller status")
        if invitation.as_ringer or invitation.relevant_game.allow_ringers:
            attending_character = CharDisplayModelChoiceField(
                world=invitation.relevant_game.cell,
                queryset=queryset,
                empty_label="Play an NPC Ringer",
                required=False)

        else:
            attending_character = CharDisplayModelChoiceField(
                world=invitation.relevant_game.cell,
                queryset=queryset,
                empty_label=None,
                help_text="Declare which character you're attending with. Private "
                           "Characters and their powers will be revealed to the "
                           "Contract creator if selected.",
                required=True,)
    return AcceptInviteForm


class ValidateAttendanceForm(forms.Form):
    attending = forms.BooleanField(label="",
                                  required=False,
                                  initial=True,)

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop('game')
        super(ValidateAttendanceForm, self).__init__(*args, **kwargs)
        self.fields['player'] = forms.ModelChoiceField(queryset=self.game.invitations.all(),
                                        required=False)
        self.fields['character'] = forms.ModelChoiceField(Character.objects.filter(player__in=self.game.invitations.filter()),
                                           empty_label="NPC Ringer",
                                           required=False)
        self.fields['character'].widget.attrs['hidden'] = True
        self.fields['player'].widget.attrs['hidden'] = True

    def attendance(self):
        return self.initial['game_attendance']

class DeclareOutcomeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # self.initial is set in super
        super(DeclareOutcomeForm, self).__init__(*args, **kwargs)
        attendance = self.initial['game_attendance']
        mvp_disabled = False
        if attendance.attending_character:
            self.fields['outcome'] = forms.ChoiceField(choices=OUTCOME[:4])
        else:
            self.fields['outcome'] = forms.ChoiceField(choices=OUTCOME[4:6])
            mvp_disabled = True
        self.fields['MVP'] = forms.BooleanField(label="Award Commission",
                                                required=False,
                                                help_text='The Contractor awarded Commission gets +2 Exp. '
                                                          'Select whoever you\'d like (MVP, funniest line, achieved secondary objective, etc).',
                                                disabled=mvp_disabled)
        self.fields['hidden_attendance'] = forms.ModelChoiceField(self.initial['game_attendance'].relevant_game.game_attendance_set.all(),
                                                   required=False)
        self.fields['hidden_attendance'].widget.attrs['hidden'] = True

    notes = forms.CharField(label='Notes',
                            max_length=500,
                            required=False,
                            help_text='Spoiler-free notes about the character\'s experience in the Contract (eg. They lost their hand, went insane, found a million bucks, etc)')
    def attendance(self):
        return self.initial['game_attendance']

class GameFeedbackForm(forms.Form):
    scenario_notes = forms.CharField(label='Scenario Notes',
                            max_length=10000,
                            widget=forms.Textarea,
                            required=False,
                            help_text='Notes about your experience running this Scenario. Geared toward other GMs. Spoilers A-OK')

def make_allocate_improvement_form(user):
    class AllocateImprovementForm(forms.Form):
        users_living_character_ids = [char.id for char in user.character_set.filter(is_deleted=False).all() if
                                      not char.is_dead() and char.improvement_ok()]
        queryset = Character.objects.filter(id__in=users_living_character_ids)
        chosen_character = forms.ModelChoiceField(queryset=queryset,
                                                  label="Chosen Contractor",
                                                     empty_label=None,
                                                     help_text="Declare which Contractor should recieve the Improvement. "
                                                               "Once confirmed, this action cannot be undone. "
                                                               "Only living Contractors that have fewer than one Improvement for every two Victories appear in this list.",
                                                     required=True)
    return AllocateImprovementForm

def make_who_was_gm_form(cell):
    class WhoWasGMForm(forms.Form):
        queryset = cell.cellmembership_set.all()
        gm = forms.ModelChoiceField(queryset=queryset,
                                      label="Who ran the Contract?",
                                      empty_label="Select a GM",
                                      required=True)
    return WhoWasGMForm

class CellMemberAttendedForm(forms.Form):
    player_id = forms.CharField(label=None,
                            max_length=200,
                            widget=forms.HiddenInput(),
                            required=True,)
    attended = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(CellMemberAttendedForm, self).__init__(*args, **kwargs)
        self.fields['attended'].label = self.initial["username"]

class OutsiderAttendedForm(forms.Form):
    username = forms.CharField(label=None,
                               max_length=200,
                               required=False,)

def make_archive_game_general_info_form(gm):
    class ArchiveGeneralInfoForm(forms.Form):
        gm_id = forms.CharField(label=None,
                                    max_length=200,
                                    widget=forms.HiddenInput(),
                                    required=True,
                                    initial=gm.id)
        scenario = ScenarioModelChoiceField(queryset=gm.scenario_set.all(),
                                            empty_label="Create New Scenario",
                                            required=False,
                                            help_text='Select the Scenario that the GM used.')
        date_format = '%m/%d/%Y %I:%M %p'
        title = forms.CharField(label='Contract Name',
                                max_length=100,
                                help_text='The Contract\'s name.')
        occurred_time = forms.DateTimeField(label='Date Played',
                                            widget=DateTimePicker(options=False, format=date_format),
                                            input_formats=[date_format],
                                            help_text='When did this Contract occur?')
        timezone = forms.ChoiceField(
            label= ("My Timezone"),
            choices=settings.ACCOUNT_TIMEZONES,
            required=False,
            initial=timezone.get_current_timezone()
        )

    return ArchiveGeneralInfoForm


def get_archival_outcome_form(game_id):
    class ArchivalOutcomeForm(forms.Form):
        player_id = forms.CharField(label=None,
                                max_length=200,
                                widget=forms.HiddenInput(),
                                required=True,)
        attendance_id = forms.CharField(label=None,
                                max_length=200,
                                widget=forms.HiddenInput(),
                                required=False,)

        attending_character = CharDisplayModelChoiceField(queryset=Character.objects.all(),
                                                        empty_label="Played a Ringer",
                                                        help_text="Declare which character this player brought.",
                                                        required=False)
        outcome = forms.ChoiceField(choices=OUTCOME)
        MVP = forms.BooleanField(label="Award Commission",
                                required=False,
                                help_text='The Contractor awarded Commission gets +2 Exp. '
                                          'Select whoever you\'d like (MVP, funniest line, achieved secondary objective, etc).',
                                 disabled=game_id < EXP_V1_V2_GAME_ID)
        notes = forms.CharField(label='Notes',
                                max_length=500,
                                required=False,
                                help_text='Spoiler-free notes about the character\'s experience in the Contract (eg. They lost '
                                          'their hand, went insane, found a million bucks, etc)')

        def __init__(self, *args, **kwargs):
            super(ArchivalOutcomeForm, self).__init__(*args, **kwargs)
            # user may have declared character dead or deleted after the game ended, so allow selecting dead characters
            if "attendance_id" in self.initial and self.initial["attendance_id"]:
                queryset = self.initial["invited_player"].character_set.distinct()
            else:
                queryset = self.initial["invited_player"].character_set\
                    .exclude(character_death__is_void = False, character_death__game_attendance__isnull = False)\
                    .distinct()
            self.fields['attending_character'].queryset = queryset

    return ArchivalOutcomeForm

class RsvpAttendanceForm(forms.Form):
    pass