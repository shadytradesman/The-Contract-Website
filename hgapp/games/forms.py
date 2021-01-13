from django import forms

from characters.models import HIGH_ROLLER_STATUS
from django.forms import ModelChoiceField
from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import datetime
from account.conf import settings
from django.utils import timezone

from games.models import Scenario

from games.models import GAME_STATUS, OUTCOME, ScenarioTag

from characters.models import Character

from games.models import Game_Attendance

from bootstrap3_datetime.widgets import DateTimePicker

from overrides.widgets import CustomStylePagedown

from tinymce.widgets import TinyMCE

class ScenarioModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.choice_txt()

class CreateScenarioForm(forms.Form):
    title = forms.CharField(label='Title',
                           max_length=130,
                           help_text='This Scenario\'s title. This may be seen by people who have not played the Scenario.')
    summary = forms.CharField(label='Summay',
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

def make_game_form(user, game_status):
    class CreateGameForm(forms.Form):
        date_format= '%m/%d/%Y %I:%M %p'
        title = forms.CharField(label='Game Name',
                               max_length=100,
                               help_text='The Game\'s Name.',
                               required=False,)
        hook = forms.CharField(label='Invitation Text',
                               widget=forms.Textarea,
                               max_length=5000,
                               help_text='Entice Players to RSVP or provide information.')


        timezone = forms.ChoiceField(
            label= ("My Timezone"),
            choices=settings.ACCOUNT_TIMEZONES,
            required=False,
            initial=user.account.timezone
        )
        queryset = user.cell_set.all()
        if game_status == str(GAME_STATUS[0][0]):
            scenario = ScenarioModelChoiceField(queryset=user.scenario_set.all(),
                                              empty_label="Create New Scenario",
                                              required=False,
                                              help_text='Select the Scenario that the game will follow.')
            scheduled_start_time = forms.DateTimeField(widget=DateTimePicker(options=False),
                                                       input_formats=[date_format],
                                                       help_text='For planning only. Places no restrictions on starting the Game.')
            open_invitations = forms.BooleanField(label="Open Invitations",
                                                  required=False,
                                                  initial=True,
                                                  help_text="If checked, Players will be able to invite themselves to the Game. "
                                                            "You will still be able to declare which Characters may actually attend as you start the Game.",)
            cell = forms.ModelChoiceField(queryset=queryset,
                                          empty_label="Select a Cell",
                                          help_text="Select a Cell for this Game. This defines the setting of the Game. "
                                                    "Cell leaders have the power to edit or void the Games "
                                                    "run in their cells.",
                                          required=True)

            invite_all_members = forms.BooleanField(initial=True,
                                                    required=False,
                                                    label='Invite all Cell Members',
                                                    help_text="Automatically invite all members of the chosen Cell to "
                                                              "this Game.",)
            required_character_status = forms.ChoiceField(choices=HIGH_ROLLER_STATUS,
                                                          help_text='Players will only be able to RSVP with Contractors of the selected Status.')
        else:
            scheduled_start_time = forms.DateTimeField(initial=datetime.today(),
                                                   disabled=True,
                                                   help_text='You can no longer change the scheduled start time.',
                                                   required=False)
            open_invitations = forms.BooleanField(label="Open Invitations",
                                                  required=False,
                                                  disabled=True,
                                                  initial=True,
                                                  help_text="Invites are closed.", )
            invite_all_members = forms.BooleanField(disabled=True,
                                                    help_text="Invites are closed.",
                                                    required=False,
                                                    )
            required_character_status = forms.ChoiceField(disabled=True,
                                                          choices=HIGH_ROLLER_STATUS,
                                                          help_text='You can no longer change required Status.')

        def default_date(self):
            if self.initial:
                #if you pass this in with the same name as the field, you get initial value issues
                return self.initial['start_time'].strftime(self.date_format)
            return None

    return CreateGameForm


def make_accept_invite_form(invitation):
    class AcceptInviteForm(forms.Form):
        users_living_character_ids = [char.id for char in invitation.invited_player.character_set.filter(is_deleted=False).all() if not char.is_dead()]
        required_status = invitation.relevant_game.required_character_status
        if required_status == HIGH_ROLLER_STATUS[0][0]:
            queryset = Character.objects.filter(id__in=users_living_character_ids)
        elif required_status == HIGH_ROLLER_STATUS[1][0] or required_status == HIGH_ROLLER_STATUS[2][0]:
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(status__in=[HIGH_ROLLER_STATUS[1][0], HIGH_ROLLER_STATUS[2][0]])
        else:
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(status=invitation.relevant_game.required_character_status)
        if invitation.as_ringer:
            attending_character = forms.ModelChoiceField(
                queryset=queryset,
                 empty_label="Play an NPC Ringer",
                 required=False)
        else:
            attending_character = CharacterModelChoiceField(queryset=queryset,
                                                     empty_label=None,
                                                     help_text="Declare which character you're attending with. Private "
                                                               "Characters and their powers will be revealed to the "
                                                               "Game creator if selected.",
                                                     required=True)
    return AcceptInviteForm

class CharacterModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


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
        if attendance.attending_character:
            self.fields['outcome'] = forms.ChoiceField(choices=OUTCOME[:4])
        else:
            self.fields['outcome'] = forms.ChoiceField(choices=OUTCOME[4:6])
        self.fields['hidden_attendance'] = forms.ModelChoiceField(self.initial['game_attendance'].relevant_game.game_attendance_set.all(),
                                                   required=False)
        self.fields['hidden_attendance'].widget.attrs['hidden'] = True

    notes = forms.CharField(label='Notes',
                            max_length=500,
                            required=False,
                            help_text='Spoiler-free notes about the character\'s experience in the game (eg. They lost their hand, went insane, found a million bucks, etc)')
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
                                                     empty_label=None,
                                                     help_text="Declare which Character should recieve the Improvement. "
                                                               "Once confirmed, this action cannot be undone. "
                                                               "NOTE: only living characters that have less than twice as many rewards as victories appear in this list.",
                                                     required=True)
    return AllocateImprovementForm

def make_who_was_gm_form(cell):
    class WhoWasGMForm(forms.Form):
        queryset = cell.cellmembership_set.all()
        gm = forms.ModelChoiceField(queryset=queryset,
                                      label="Which Cell member ran the Game?",
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
        title = forms.CharField(label='Game Name',
                                max_length=100,
                                help_text='The Game\'s name.')
        occurred_time = forms.DateTimeField(label='Date Played',
                                            widget=DateTimePicker(options=False),
                                            input_formats=[date_format],
                                            help_text='When did this Game occur?')
        timezone = forms.ChoiceField(
            label= ("My Timezone"),
            choices=settings.ACCOUNT_TIMEZONES,
            required=False,
            initial=timezone.get_current_timezone()
        )
    return ArchiveGeneralInfoForm

class ArchivalOutcomeForm(forms.Form):
    player_id = forms.CharField(label=None,
                            max_length=200,
                            widget=forms.HiddenInput(),
                            required=True,)

    attending_character = CharacterModelChoiceField(queryset=Character.objects.all(),
                                                    empty_label="Played a Ringer",
                                                    help_text="Declare which character this player brought.",
                                                    required=False)
    outcome = forms.ChoiceField(choices=OUTCOME)
    notes = forms.CharField(label='Notes',
                            max_length=500,
                            required=False,
                            help_text='Spoiler-free notes about the character\'s experience in the game (eg. They lost '
                                      'their hand, went insane, found a million bucks, etc)')

    def __init__(self, *args, **kwargs):
        super(ArchivalOutcomeForm, self).__init__(*args, **kwargs)
        # user may have declared character dead after the game ended, so allow selecting dead characters
        queryset = self.initial["invited_player"].character_set.filter(is_deleted=False)\
            .exclude(character_death__is_void = False, character_death__game_attendance__isnull = False)\
            .distinct()
        self.fields['attending_character'].queryset = queryset

class RsvpAttendanceForm(forms.Form):
    pass