from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from overrides.widgets import CustomStylePagedown

from games.game_utilities import get_character_contacts
from characters.models import Character, BasicStats, Character_Death, BattleScar, PORT_STATUS, StockBattleScar, GIVEN,\
    STOLEN, LOOTED, LOST, DESTROYED, RECOVERED, REPAIRED
from cells.models import Cell

ATTRIBUTE_VALUES = {
    "Brawn": (
        ('1', '1 - Puny'),
        ('2', '2 - Average'),
        ('3', '3 - Solid'),
        ('4', '4 - Musclebound'),
        ('5', '5 - Giant'),
    ),
    "Charisma": (
        ('1', '1 - Off-putting'),
        ('2', '2 - Average'),
        ('3', '3 - Outgoing'),
        ('4', '4 - Magnetic'),
        ('5', '5 - Unhatable'),
    ),
    "Dexterity": (
        ('1', '1 - Clumsy'),
        ('2', '2 - Average'),
        ('3', '3 - Nimble'),
        ('4', '4 - Quick'),
        ('5', '5 - Lightning-fast'),
    ),
    "Intelligence": (
        ('1', '1 - Simple'),
        ('2', '2 - Average'),
        ('3', '3 - Bright'),
        ('4', '4 - Intellectual'),
        ('5', '5 - Genius'),
    ),
    "Perception": (
        ('1', '1 - Oblivious'),
        ('2', '2 - Average'),
        ('3', '3 - Attentive'),
        ('4', '4 - Vigilant'),
        ('5', '5 - Informed'),
    ),
    "Wits": (
        ('1', '1 - Dull'),
        ('2', '2 - Average'),
        ('3', '3 - Resourceful'),
        ('4', '4 - Decisive'),
        ('5', '5 - Reflexive'),
    ),
    "default": (
        ('1', '1 - Below Average'),
        ('2', '2 - Average'),
        ('3', '3 - Above Average'),
        ('4', '4 - Exceptional'),
        ('5', '5 - World Class'),
    ),
}

PHYS_MENTAL = (
    ("0", "Physical"),
    ("1", "Mental"),
)

def make_character_form(user, existing_character=None, supplied_cell=None):
    class CharacterForm(ModelForm):
        class Meta:
            model = Character
            fields = ('name', 'private', 'tagline', 'appearance', 'age', 'concept_summary', 'ambition', 'paradigm',
                      'residence', 'languages', 'insanities', 'disabilities', 'current_alias', 'previous_aliases',
                      'resources', 'contacts', 'equipment', 'total_encumbrance', 'max_encumbrance', 'wish_list',
                      'to_do_list', 'contracts', 'pronoun')
            help_texts = {
                'name': _('Name'),
                'private': _("If checked, this Contractor will only be viewable by their Playgroup's leaders and any GMs "
                             "running Games for them."),
                'pronoun': _(""),
                'tagline': _('A subtitle that introduces your Contractor in a flavorful way'),
                'appearance': _('A brief description of your Contractor\'s outward appearance.'),
                'concept_summary': _('Archetype Summary (ex: "skater punk werewolf", "cannibal chef", or "golden-age comic book hero")'),
                'ambition': _('Ambition. Why does this Contractor risk their life in the Games? Focus outward: how do they want to '
                              'change the world?'),
                'age': _("Age"),
                'paradigm': _('How do the character\'s powers work?'),
                'residence': _('Where the character lives'),
                'languages': _('List of languages the character speaks'),
                'insanities': _('List of instabilities and insanities the character possesses'),
                'disabilities': _('List of disabilities and battle scars the character possesses'),
                'current_alias': _('The character\'s current identity'),
                'previous_aliases': _('The character\'s previous aliases'),
                'resources': _('How much money does this character have access to each game?'),
                'contacts': _('List of other characters that this character has the contact information for'),
                'total_encumbrance': _('The weight of the character\'s equipment'),
                'max_encumbrance': _('The maximum amount that the character can carry'),
                'wish_list': _('List of wants and dreams'),
                'to_do_list': _('List of things to do'),
                'contracts': _('Legal and supernatural contracts this character is entered into'),
            }
            widgets = {
                'name': forms.TextInput(attrs={'class': 'form-control'}),
                'concept_summary':forms.TextInput(attrs={'class': 'form-control '}),
                'pronoun': forms.Select(attrs={'class': 'form-control '}),
                'ambition': forms.TextInput(attrs={'class': 'form-control '}),
                'age': forms.TextInput(attrs={'class': 'form-control '}),
                'appearance': forms.TextInput(attrs={'class': 'form-control '}),
                'equipment': CustomStylePagedown(),
                'notes': CustomStylePagedown(),
            }

    form = CharacterForm
    if user.is_authenticated:
        if existing_character:
            queryset = existing_character.player.cell_set.all()
        else:
            queryset = user.cell_set.all()
        cell = forms.ModelChoiceField(queryset=queryset,
                                      widget=forms.Select(attrs={'class': 'form-control'}),
                                      empty_label="Nowhere",
                                      required=False,
                                      )
        if supplied_cell:
            cell.initial = supplied_cell
        if existing_character:
            cell.initial = existing_character.cell
        elif queryset.first():
            cell.initial = queryset.first()
    else:
        cell = forms.ModelChoiceField(queryset=Cell.objects.none(),
                                      widget=forms.Select(attrs={'class': 'form-control'}),
                                      empty_label="Nowhere",
                                      required=False,
                                      )
    form.base_fields["cell"] = cell

    return form

class CharacterDeathForm(ModelForm):
    class Meta:
        model = Character_Death
        fields = ('obituary', 'cause_of_death')
        help_texts = {
            'obituary': _('Honor the dearly departed'),
            'cause_of_death': _('They were killed by. . .')
        }
        widgets = {
            'obituary': forms.Textarea,
        }

    def __init__(self, *args, **kwargs):
        super(CharacterDeathForm, self).__init__(*args, **kwargs)
        if self.initial:
            self.fields['is_void'] = forms.BooleanField(required=False,
                                                        label="Void this death",
                                                        help_text="If this box is checked, this existing death will be voided and your character will be alive again. This will impact the precieved legitimacy of your character.")
class ConfirmAssignmentForm(forms.Form):
    pass


#Advanced stat forms
class AttributeForm(forms.Form):
    value = forms.ChoiceField(choices=(()),
                              widget=forms.Select(attrs={'class': 'form-control '}))
    attribute_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),) # hidden field to track which attribute we are editing.
    previous_value_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),required=False)

    def __init__(self, *args, **kwargs):
        super(AttributeForm, self).__init__(*args, **kwargs)
        if "attribute" in self.initial:
            attribute = self.initial["attribute"]
            self.fields['value'].label = attribute.name
            if attribute.name in ATTRIBUTE_VALUES:
                self.fields['value'].choices = ATTRIBUTE_VALUES[attribute.name]
            else:
                self.fields['value'].choices = ATTRIBUTE_VALUES["default"]
        if 'previous_value_id' in self.initial:
            self.fields['previous_value_id'].initial = self.initial['previous_value_id']

def get_ability_form(ability_max):
    class AbilityForm(forms.Form):
        ability_id = forms.IntegerField(label=None,
                                        widget=forms.HiddenInput(),
                                        required=False) # hidden field to track which abilities we are editing.
        value = forms.IntegerField(initial=0,
                                   validators=[MaxValueValidator(ability_max), MinValueValidator(0)],
                                   widget=forms.NumberInput(attrs={'class': 'ability-value-input form-control'}))
        value_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),required=False)
        name = forms.CharField(max_length=50,
                               required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control sec-ability-name'}))
        description = forms.CharField(max_length=250,
                                      required=False,
                                      widget=forms.TextInput(attrs={'class': 'form-control sec-ability-desc'}))

        def __init__(self, *args, **kwargs):
            super(AbilityForm, self).__init__(*args, **kwargs)
            if 'ability' in self.initial:
                ability = self.initial["ability"]
                self.initial["ability_name"] = ability.name
                self.initial["ability_is_primary"] = ability.is_primary
                self.initial["ability_tutorial_text"] = ability.tutorial_text

                self.fields['name'].initial = ability.name
                self.fields['ability_id'].initial = ability.id
                self.fields['description'].widget = forms.HiddenInput()
                self.fields['name'].widget = forms.HiddenInput()
            if 'value_id' in self.initial and self.initial['value_id']:
                self.fields['value_id'].initial = self.initial['value_id']
    return AbilityForm

class QuirkForm(forms.Form):
    id = forms.IntegerField(label=None, widget=forms.HiddenInput(),) # hidden field to track which quirks we are editing.
    details_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),required=False)
    is_selected = forms.BooleanField(required=False)
    details = forms.CharField(max_length=600,
                           widget=forms.TextInput(attrs={'class': 'form-control'}),
                              required=False)

    def __init__(self, *args, **kwargs):
        super(QuirkForm, self).__init__(*args, **kwargs)
        if 'quirk' in self.initial:
            quirk = self.initial["quirk"]
            self.fields['id'].initial = quirk.id
            self.fields['is_selected'].label = quirk.name
            self.fields['is_selected'].widget = forms.CheckboxInput(attrs={'class': 'quirk-multiple-' + str(quirk.multiplicity_allowed)})
        if 'details' in self.initial:
            self.fields['details'].initial = self.initial['details']
        if 'is_selected' in self.initial:
            self.fields['is_selected'].initial = self.initial['is_selected']
        if 'details_id' in self.initial:
            self.fields['details_id'].initial = self.initial['details']

class LiabilityForm(QuirkForm):
    pass

class AssetForm(QuirkForm):
    pass

class LimitForm(forms.Form):
    checked = forms.BooleanField(required=False)
    id = forms.IntegerField(label=None, widget=forms.HiddenInput(),required=False) # hidden field to track which limit we are editing.
    limit_rev_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),required=False)

    name = forms.CharField(max_length=40,
                           required=False,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(max_length=900,
                                  required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(LimitForm, self).__init__(*args, **kwargs)
        if 'limit' in self.initial:
            limit = self.initial["limit"]
            self.fields['id'].initial = limit.id
            self.fields['checked'].label = limit.name
            self.fields['name'].initial = limit.name
            self.fields['description'].initial = limit.description
        if 'selected' in self.initial:
            self.fields['checked'].initial = self.initial['selected']
        if 'limit_rev_id' in self.initial:
            self.fields['limit_rev_id'].initial = self.initial['limit_rev_id']


# method to get floating field because field is used only on FE and never submitted to the backend.
def get_default_scar_choice_field():
    stock_scars = StockBattleScar.objects.order_by("type").all()
    options = [("", "Create Custom Scar")]
    if stock_scars.count() > 0:
        current_options = []
        current_type = stock_scars[0].get_type_display()
        for scar in stock_scars:
            if scar.get_type_display() != current_type:
                options.append((current_type, current_options))
                current_options = []
                current_type = scar.get_type_display()
            current_options.append((scar.system, scar.description))
        options.append((current_type, current_options))
    default_field = forms.ChoiceField(choices=options,
                                      label="Select Scar",
                                      required=False,)
    class DefaultScarForm(forms.Form):
        premade_scar_field = default_field
    return DefaultScarForm



class BattleScarForm(forms.Form):
    scar_description = forms.CharField(max_length=500,
                                  label="Description",
                                  widget=forms.TextInput(attrs={'class': 'form-csontrol'}))
    scar_system = forms.CharField(max_length=500,
                              label="System",
                              widget=forms.TextInput(attrs={'class': 'form-csontrol'}))


class TraumaForm(forms.Form):
    description = forms.CharField(max_length=900,
                                  label=None,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))

class SourceForm(forms.Form):
    source_id = forms.IntegerField(label=None,
                                    widget=forms.HiddenInput())  # hidden field to track which source we are editing.
    value = forms.IntegerField(initial=1,
                               validators=[MaxValueValidator(10), MinValueValidator(1)],
                               widget=forms.NumberInput(attrs={'class': 'source-value-input form-control'}))
    rev_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=False)
    name = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control source-name'}))
    def __init__(self, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)
        if 'source' in self.initial:
            source = self.initial["source"]
            self.fields['name'].initial = source.name
            self.fields['source_id'].initial = source.id
        if 'rev_id' in self.initial and self.initial['rev_id']:
            self.fields['rev_id'].initial = self.initial['rev_id']

class InjuryForm(forms.Form):
    description = forms.CharField(max_length=900,
                                  label=None,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    severity = forms.IntegerField(validators=[MaxValueValidator(20), MinValueValidator(0)],
                               widget=forms.NumberInput(attrs={'class': 'js-injury-value-input form-control', 'value': '1'}))

class SourceValForm(forms.Form):
    value = forms.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(0)])

def make_allocate_gm_exp_form(queryset):
    class AllocateGmExpForm(forms.Form):
        chosen_character = forms.ModelChoiceField(queryset=queryset,
                                                  empty_label="Save for now",
                                                  required=False,
                                                  label=None,
                                                  widget=forms.Select(attrs={'class': 'form-control '}))
        reward_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=False)

        def __init__(self, *args, **kwargs):
            super(AllocateGmExpForm, self).__init__(*args, **kwargs)
            self.fields['chosen_character'].label_from_instance = self.label_from_instance
            if 'reward' in self.initial:
                reward = self.initial["reward"]
                self.fields['reward_id'].initial = reward.id
                self.initial['reward_source'] = reward.source_blurb()
                self.initial['reward_amount'] = reward.get_value()
            else:
                raise ValueError("GM Exp form must have a supplied reward")

        @staticmethod
        def label_from_instance(obj):
            return obj.name

    return AllocateGmExpForm

class EquipmentForm(forms.Form):
    equipment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}),
                                label=None)

class BioForm(forms.Form):
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}),
                                label=None)

def make_charon_coin_form(character=None):
    initial = character.assigned_coin() if character else False
    class CharonCoinForm(forms.Form):
        spend_coin = forms.BooleanField(required=False,
                                        initial=initial)
    return CharonCoinForm

def make_character_ported_form(character=None):
    initial = character.ported if character else PORT_STATUS[0]
    class CharacterPortedForm(forms.Form):
        port_status = forms.ChoiceField(choices=PORT_STATUS,
                                        widget=forms.Select(attrs={'class': 'form-control '}),
                                        initial=initial)
    return CharacterPortedForm

class DeleteCharacterForm(forms.Form):
    pass


def make_world_element_form(cell_choices=None, initial_cell=None, for_new=True):
    class WorldElementForm(forms.Form):
        name = forms.CharField(max_length=500,
                                      label=None,
                                      widget=forms.TextInput(attrs={'class': 'form-control'}))
        description = forms.CharField(max_length=1000,
                                      label=None,
                                      widget=forms.TextInput(attrs={'class': 'form-control'}))
        system = forms.CharField(max_length=1000,
                                 label="System (optional)",
                                 required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
        cell = forms.ModelChoiceField(label="Playgroup",
                                      queryset=cell_choices,
                                      widget=forms.Select(attrs={'class': 'form-control'}),
                                      initial=initial_cell if initial_cell else cell_choices.first() if cell_choices else None,
                                      required=for_new,
                                      )
    return WorldElementForm


def make_artifact_status_form(current_status=None):
    if current_status == LOST:
        choices = (
                  ('', "No change"),
                  (RECOVERED, "Recovered"),
              )
    elif current_status == DESTROYED:
        choices = (
              ('', "No change"),
              (REPAIRED, "Repaired"),
          )
    else:
        choices = (
                     ('', 'No change'),
                     (LOST, "Lost"),
                     (DESTROYED, "Destroyed"),
                  )

    class ArtifactStatusForm(forms.Form):
        change_availability = forms.ChoiceField(
            choices=choices,
            required=False,
            widget=forms.Select(attrs={'class': 'js-item-availability-change'}),
            label="Change Availability",)
        notes = forms.CharField(max_length=1000,
                                label="Availability Change Notes",
                                required=False)
    return ArtifactStatusForm


def make_transfer_artifact_form(character, cell=None, max_quantity=0):
    character_options = get_character_contacts(character)
    character_options = set([x.pk for x in character_options.keys()])
    if character.cell:
        character_options.update(cell.character_set.exclude(player=character.player).values_list('id', flat=True))
    if character.pk in character_options:
        character_options.remove(character.pk)

    class TransferArtifactForm(forms.Form):
        transfer_type = forms.ChoiceField(
            label="These consumables were" if max_quantity > 1 else "This item was",
            choices=(
                (GIVEN, "Given to"),
                (STOLEN, "Stolen by"),
                (LOOTED, "Looted by"),),
            required=True,)
        to_character = forms.ModelChoiceField(label="Contractor",
                                      queryset=Character.objects.filter(id__in=[x for x in character_options]).order_by("name"),
                                      widget=forms.Select(attrs={'class': 'form-control'}),
                                              empty_label=None,
                                      required=True)
        quantity = forms.IntegerField(
            label="Quantity (max {})".format(max_quantity),
            initial=1,
            max_value=max_quantity,
            min_value=1,
            validators=[MaxValueValidator(max_quantity), MinValueValidator(0)],
            required=max_quantity != 0,
            widget=forms.NumberInput(attrs={'class': "form-inline"}) if max_quantity != 0 else forms.HiddenInput())
        notes = forms.CharField(
            max_length=1000,
            label="Notes (optional)",
            required=False)

    return TransferArtifactForm


def make_consumable_use_form(artifact):
    class UseConsumableForm(forms.Form):
        new_quantity = forms.IntegerField(
            initial=artifact.quantity-1,
            validators=[MaxValueValidator(artifact.quantity-1), MinValueValidator(artifact.quantity-1)],
            required=True,
            widget=forms.HiddenInput())

    return UseConsumableForm
