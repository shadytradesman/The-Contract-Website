from django import forms
from itertools import groupby

from django.forms.models import ModelChoiceIterator
from itertools import chain

from django.forms import ModelChoiceField
from account.conf import settings
from django.utils import timezone

from games.models import OUTCOME, ScenarioTag, REQUIRED_HIGH_ROLLER_STATUS, INVITE_MODE, GameMedium, REQ_STATUS_ANY, \
    REQ_STATUS_NEWBIE, REQ_STATUS_NOVICE, REQ_STATUS_SEASONED, REQ_STATUS_PROFESSIONAL, REQ_STATUS_VETERAN, \
    REQ_STATUS_NEWBIE_OR_NOVICE, WIKI_EDIT_MODE
from .games_constants import EXP_V1_V2_GAME_ID
from characters.models import Character, ELEMENT_TYPE, HIGH_ROLLER_STATUS
from characters.forms import LooseEndForm

from bootstrap3_datetime.widgets import DateTimePicker

from tinymce.widgets import TinyMCE

class ScenarioModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.choice_txt()

SCENARIO_TINYMCE_SETTINGS = {
    "theme": "silver",
    "height": 500,
    "menubar": False,
    "browser_spellcheck": True,
    "contextmenu": "useBrowserSpellcheck",
    "images_upload_handler": """
    function (blobInfo, success, failure) {
    var xhr, formData;

    xhr = new XMLHttpRequest();
    xhr.withCredentials = false;
    xhr.open('POST', "/image/tiny_upload/");

    xhr.onload = function() {
        var json;

        if (xhr.status != 200) {
            failure('HTTP Error: ' + xhr.status);
            return;
        }

        json = JSON.parse(xhr.responseText);

        if (!json || typeof json.location != 'string') {
            failure('Invalid JSON: ' + xhr.responseText);
            return;
        }

        success(json.location);
    };

    formData = new FormData();
    formData.append('file', blobInfo.blob(), blobInfo.filename());
    formData.append('scenario', JSON.parse(document.getElementById('scenarioId').textContent));
    // append CSRF token in the form data
    function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
    }
    let csrfValue = getCookie("csrftoken");
    formData.append('csrfmiddlewaretoken', csrfValue);

    xhr.send(formData);
}
    """,
    "plugins": "advlist,autolink,lists,link,image,charmap,print,preview,anchor,"
               "searchreplace,visualblocks,code,fullscreen,insertdatetime,media,table,paste,"
               "code,help,wordcount",
    "toolbar": "formatselect fontselect fontsizeselect | "
               "bold italic strikethrough underline removeformat | backcolor forecolor | alignleft aligncenter "
               "| bullist numlist link unlink | table | image uploadimage"
               " | help ",
    "paste_data_images": True,
    "toolbar_mode": 'wrap',
    'content_css': "/static/css/site.css,/static/games/scenario_widget.css",
}

new_scenario_widget = TinyMCE(
    attrs={
        'cols': 80,
        'rows': 20
    },
    mce_attrs=SCENARIO_TINYMCE_SETTINGS,
)

class ScenarioWriteupForm(forms.Form):
    overview = forms.CharField(label='Overview',
                               required=False,
                               widget=new_scenario_widget,
                               max_length=99000,
                               help_text='Provide a high-level outline of the Scenario that gives GMs a clear idea of how it runs.')
    backstory = forms.CharField(label='Backstory',
                                required=False,
                                widget=new_scenario_widget,
                                max_length=99000,
                                help_text='This is GM pre-reading. Describe the characters and events that led to the '
                                          'situation the Contractors encounter.')
    introduction = forms.CharField(label='Intro and Briefing',
                                   required=False,
                                   widget=new_scenario_widget,
                                   max_length=99000,
                                   help_text='How are the Contractors gathered? How are they briefed? <b>What counts'
                                             ' as a Victory, and what causes Failure?</b>')
    mission = forms.CharField(label='Mission',
                              required=False,
                              widget=new_scenario_widget,
                              max_length=99000,
                              help_text='This is the bulk of the Contract. Include guidance on scenes, characters, and '
                                        'rolls. Remember to use heading levels in the editor '
                                        'to split it into easy-to-navigate sub-sections.')
    aftermath = forms.CharField(label='Aftermath',
                                required=False,
                                widget=new_scenario_widget,
                                max_length=99000,
                                help_text='What happens after the Contract is over? What if Contractors return to the scene of the crime? '
                                          'Provide guidance for Loose Ends or Moves.')


def make_create_scenario_form(existing_scenario=None):
    class CreateScenarioForm(forms.Form):
        title = forms.CharField(label='Title',
                               max_length=130,
                               help_text='This Scenario\'s title. This may be seen by people who have not played the Scenario.')
        summary = forms.CharField(label='Summary',
                                  max_length=400,
                                  required=False,
                                  help_text="Summarize the Scenario so that people who have already played it can recognize it.")
        exchange_information = forms.CharField(label='Exchange blurb',
                                  max_length=1000,
                                  required=False,
                                  help_text="SPOILER-FREE information to display to prospective GMs in the Scenario Exchange. "
                                            "E.g. \"A great Scenario for new GMs.\" "
                                            "NOTE: all Players and "
                                            "anonymous users will be able to read this on the exchange, so assume you are telling this to all "
                                            "would-be Players.")
        description = forms.CharField(label='Write-up',
                                      required=False,
                                widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                                max_length=70000,
                                help_text='Describe the Scenario in detail. Win conditions, enemies, background, etc.')
        objective = forms.CharField(label='Objective',
                                  max_length=400,
                                  required=True,
                                  help_text="What is the Contractors' goal in this Scenario? Be very careful with your wording.")
        max_players = forms.IntegerField(label = "Max Players", initial=4)
        min_players = forms.IntegerField(label = "Minimum Players", initial=2)
        suggested_character_status = forms.ChoiceField(label = "Required Status",
                                                       choices=HIGH_ROLLER_STATUS,
                                                       help_text='Must be this tall to ride')
        is_highlander = forms.BooleanField(label = "Highlander",
                                           required=False,
                                           help_text = "Only one Contractor can achieve victory")
        edit_mode_choices = list(WIKI_EDIT_MODE)
        if existing_scenario is not None and existing_scenario.is_on_exchange:
            edit_mode_choices = edit_mode_choices[1:]
        edit_mode_choices.insert(0, ('', 'No community editing'))
        community_edit_mode = forms.ChoiceField(label="Allow Community Edits",
                                                choices=edit_mode_choices,
                                                required=False,
                                                help_text="Determines who else can edit this Scenario's writeup for formatting, typos, rules updates, etc. "
                                                          "You can always edit your own Scenario, and only you "
                                                          "can edit the primary details of the Scenario such as "
                                                          "its summary, objective, and title. A full "
                                                          "revision history is kept, and you may revert any edits at will.")
        is_rivalry = forms.BooleanField(label = "Rivalry",
                                        required=False,
                                        help_text="The Contractors may have different or opposing goals")
        requires_ringer = forms.BooleanField(label = "Requires Ringer",
                                             required=False,
                                             help_text="One Player must play an NPC instead of their Contractor")
        tags = forms.ModelMultipleChoiceField(queryset=ScenarioTag.objects.order_by("tag").all(),
                                              required=False,
                                              widget=forms.CheckboxSelectMultiple)
    return CreateScenarioForm

class ScenarioElementForm(forms.Form):
    designation = forms.CharField(max_length=120,
                                  widget=forms.HiddenInput(),
                                  required=False)
    is_deleted = forms.BooleanField(required=False, label="Delete")

    def clean(self):
        if self.cleaned_data["is_deleted"]:
            # we don't care about other field validations if we are deleting it.
            self._errors = []
        else:
            return super().clean()


class ScenarioConditionCircumstanceForm(ScenarioElementForm):
    name = forms.CharField(max_length=150, required=True)
    description = forms.CharField(max_length=5000, required=True)
    system = forms.CharField(max_length=1000, required=True)


class ScenarioLooseEndForm(LooseEndForm, ScenarioElementForm):
    pass


class RevertToEditForm(forms.Form):
    writeup_id = forms.IntegerField(label=None,
                                    widget=forms.HiddenInput(),
                                    required=True,)


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


class ShareScenarioForm(forms.Form):
    username = forms.CharField(label='Player\'s Username', max_length=200, required=True)


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
            help_text= ("This will set your account's timezone settings, so always enter YOUR timezone."),
            choices=settings.ACCOUNT_TIMEZONES,
            required=False,
            initial=user.account.timezone
        )
        all_cells = user.cell_set.filter(cellmembership__is_banned=False).all()
        cell_ids = {cell.id for cell in all_cells if cell.player_can_run_games(user)}
        queryset = user.cell_set.filter(id__in=cell_ids).all()
        scenario = ScenarioModelChoiceField(queryset=user.scenario_set.filter(scenario_discovery__is_spoiled=True).order_by("title").all(),
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
                                                "to pocket realms, other planets, or similar. "
                                                "Playgroup leaders have the power to edit or void Contracts "
                                                "run in their Playgroup.",
                                      required=True)

        invite_all_members = forms.BooleanField(initial=True,
                                                required=False,
                                                label='Invite all Playgroup Members',
                                                help_text="Automatically send an invite to all Playgroup members "
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
        allow_ringers = forms.BooleanField(initial=False,
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

class CharDisplayByCellModelChoiceField(ModelChoiceField):
    def __init__(self, world=None, *args, **kwargs):
        self.iterator = buildContractorChoiceIterator(world)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, character):
        return "{} ({} Victories)".format(character.name, character.number_of_victories())


def buildContractorChoiceByActiveIterator(active_characters, previous_characters):
    class ContractorChoiceIterator(ModelChoiceIterator):
        def __len__(self):
            return self.queryset.count()

        def __iter__(self):
            queryset = chain(active_characters, previous_characters)
            groups = groupby(queryset, key=lambda x: x in active_characters)
            for active, contractors in groups:
                yield [
                    "Active Contractors" if active else "Previous Contractors",
                    [
                        (contractor.id, contractor.name)
                        for contractor in contractors
                    ]
                ]
    return ContractorChoiceIterator

class CharDisplayByActiveModelChoiceField(ModelChoiceField):
    def __init__(self, active_characters, previous_characters, *args, **kwargs):
        self.iterator = buildContractorChoiceByActiveIterator(active_characters, previous_characters)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, character):
        return "{}".format(character.name)


def make_accept_invite_form(invitation):
    class AcceptInviteForm(forms.Form):
        queryset = invitation.get_available_characters()
        if invitation.as_ringer or invitation.relevant_game.allow_ringers:
            attending_character = CharDisplayByCellModelChoiceField(
                world=invitation.relevant_game.cell,
                queryset=queryset,
                empty_label="Play an NPC Ringer",
                required=False)

        else:
            attending_character = CharDisplayByCellModelChoiceField(
                world=invitation.relevant_game.cell,
                queryset=queryset,
                empty_label=None,
                help_text="Declare which character you're attending with. Private "
                           "Characters and their Gifts will be revealed to the "
                           "GM if selected.",
                required=True,)
    return AcceptInviteForm


def make_grant_stock_element_form(scenario, gm):
    class GrantStockElementForm(forms.Form):
        active_characters = [x for x in scenario.get_active_characters_for_gm(gm) if x.player_can_edit(gm)]
        previous_characters = [x for x in scenario.get_finished_characters_for_gm(gm) if x.player_can_edit(gm)]
        contractor = CharDisplayByActiveModelChoiceField(
            active_characters=active_characters,
            previous_characters=previous_characters,
            queryset=Character.objects.filter(pk__in=[x.pk for x in chain(active_characters,previous_characters)]),
            empty_label=None,
            required=True,)
    return GrantStockElementForm

class ValidateAttendanceForm(forms.Form):
    attending = forms.BooleanField(label="",
                                  required=False,
                                  initial=True,)

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop('game')
        super(ValidateAttendanceForm, self).__init__(*args, **kwargs)
        self.fields['player'] = forms.ModelChoiceField(queryset=self.game.invitations.all(),
                                        required=False)
        self.fields['character'] = forms.ModelChoiceField(Character.objects.filter(pk__in=self.game.attended_by.values_list('pk')),
                                           empty_label="NPC Ringer",
                                           required=False)
        self.fields['character'].widget.attrs['hidden'] = True
        self.fields['player'].widget.attrs['hidden'] = True

    def attendance(self):
        return self.initial['game_attendance']


def make_grant_element_form(character_queryset):
    class GrantElementForm(forms.Form):
        grant_to_characters = forms.ModelMultipleChoiceField(
            queryset=character_queryset,
            widget=forms.CheckboxSelectMultiple(),
            label="Grant to Contractors",
            required=False,
        )
        element_id = forms.CharField(label=None,
                                     max_length=200,
                                     widget=forms.HiddenInput(),
                                     required=True,)
    return GrantElementForm


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


def make_allocate_improvement_form(user, cell_id=None):
    class AllocateImprovementForm(forms.Form):
        users_living_character_ids = [char.id for char in user.character_set.filter(is_deleted=False, is_dead=False).all() if char.improvement_ok()]
        queryset = Character.objects.filter(id__in=users_living_character_ids, cell_id=cell_id)
        chosen_character = forms.ModelChoiceField(queryset=queryset,
                                                  label="Chosen Contractor",
                                                  empty_label=None,
                                                  help_text="Declare which Contractor should receive the Improvement. "
                                                            "Once confirmed, this action cannot be undone. "
                                                            "Only living Contractors with total Gifts and Improvements totaling fewer than 2 for every Contract victory appear in this list. Improvements from a specific Playgroup can only be granted to Contractors in that Playgroup.",
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


class SpoilScenarioForm(forms.Form):
    pass


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
        cell = ModelChoiceField(queryset=gm.cell_set.exclude(cellmembership__is_banned=True).all(),
                                required=True,
                                label="Playgroup",
                                empty_label=None,
                                help_text='Select the Playgroup.')
        date_format = '%m/%d/%Y %I:%M %p'
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

        attending_character = CharDisplayByCellModelChoiceField(queryset=Character.objects.all(),
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


class SubmitScenarioForm(forms.Form):
    exchange_information = forms.CharField(label='Exchange blurb',
                                       max_length=1000,
                                       required=False,
                                       help_text="SPOILER-FREE information to display to prospective GMs in the Scenario Exchange. "
                                                 "E.g. \"A great Scenario for new GMs.\" "
                                                 "All Players and "
                                                 "anonymous users will be able to read this on the exchange, so assume you are telling this to all "
                                                 "would-be Players. Can be edited in the Scenario writeup once set here.")


def make_edit_move_form(gm, cell=None):
    if cell:
        queryset = cell.character_set.exclude(player=gm).exclude(num_games=0).exclude(character_death__isnull=False).all()
    else:
        queryset = None

    class EditMoveForm(forms.Form):
        if cell:
            character = forms.ModelChoiceField(queryset=queryset,
                                               label="Who made the Move?",
                                               empty_label="Select a Contractor",
                                               required=True)
        is_private = forms.BooleanField(label="Hide Move-Maker",
                                 required=False,
                                 help_text='If checked, the name of the Contractor who made the move will be hidden.')
        title = forms.CharField(label='Move Title',
                                max_length=200,
                                help_text='The Move\'s title')
        summary = forms.CharField(label='Move Summary',
                                  widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                                  max_length=70000,
                                  help_text='Describe the events and outcome of the Move. This will appear on the Contractor\'s sheet and Journal')
    return EditMoveForm


class ScenarioApprovalForm(forms.Form):
    is_approved = forms.BooleanField(label="Approve",
                                    required=False,
                                    help_text='If checked, Scenario is added to the exchange. If not, Scenario is rejected.')
    feedback = forms.CharField(label='Feedback',
                                 max_length=8000,
                                 widget=forms.Textarea,
                                 required=False,
                                 help_text='Will be shown to the person who submitted the Scenario if rejected.')
