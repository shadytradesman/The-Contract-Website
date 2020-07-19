from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from overrides.widgets import CustomStylePagedown

from characters.models import Character, BasicStats, Character_Death, BattleScar

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

def make_character_form(user, existing_character=None):
    class CharacterForm(ModelForm):
        class Meta:
            model = Character
            fields = ('name', 'private', 'tagline', 'appearance', 'age', 'concept_summary', 'ambition', 'paradigm',
                      'residence', 'languages', 'insanities', 'disabilities', 'current_alias', 'previous_aliases',
                      'resources', 'contacts', 'equipment', 'total_encumbrance', 'max_encumbrance', 'wish_list',
                      'to_do_list', 'contracts', 'background', 'notes', 'pronoun')
            help_texts = {
                'name': _('Name'),
                'private': _("If checked, Character will not be publicly viewable."),
                'pronoun': _(""),
                'tagline': _('A subtitle that introduces your Character in a flavorful way'),
                'appearance': _('A brief description of your Character\'s outward appearance.'),
                'concept_summary': _('Archetype Summary (ex: "skater punk werewolf", "cannibal chef", or "golden-age comic book hero")'),
                'ambition': _('Ambition. Why does this character risk their life in the games? Good ambitions can shape '
                              'the Character\'s interactions (ex: "drive non-humans out of the USA" is better than "become'
                              ' the ultimate fighter")'),
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
                'equipment': _('List of equipment the character has with them'),
                'total_encumbrance': _('The weight of the character\'s equipment'),
                'max_encumbrance': _('The maximum amount that the character can carry'),
                'wish_list': _('List of wants and dreams'),
                'to_do_list': _('List of things to do'),
                'contracts': _('Legal and supernatural contracts this character is entered into'),
                'background': _('History and backstory'),
                'notes': _('Misc notes'),
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
    queryset = user.cell_set.all()
    cell = forms.ModelChoiceField(queryset=queryset,
                                  empty_label="Free Agent (No Cell)",
                                  help_text="Select a Cell for your Character. "
                                            "This defines your Character's home world and allows "
                                            "Cell leaders to help you with record-keeping. "
                                            "NOTE: Cell leaders will be able to view and edit your Character.",
                                  required=False,
                                  )
    if existing_character:
        cell.initial = existing_character.cell
    form.base_fields["cell"] = cell
    return form

class CharacterDeathForm(ModelForm):
    class Meta:
        model = Character_Death
        fields = ('obituary', 'cause_of_death')
        help_texts = {
            'obituary': _('Honor the dearly departed'),
            'cause_of_death': _('Short summary of the cause of death')
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


class AbilityForm(forms.Form):
    ability_id = forms.IntegerField(label=None,
                                    widget=forms.HiddenInput(),
                                    required=False) # hidden field to track which abilities we are editing.
    value = forms.IntegerField(initial=0,
                               validators=[MaxValueValidator(5), MinValueValidator(0)],
                               widget=forms.NumberInput(attrs={'class': 'ability-value-input form-control'}))
    value_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),required=False)
    name = forms.CharField(max_length=50,
                           required=False,
                           widget=forms.TextInput(attrs={'class': 'form-control sec-ability-name'}))
    description = forms.CharField(max_length=250,
                                  required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control sec-ability-desc'}))
    phys_mental = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control sec-ability-phys'}),
                                    choices=PHYS_MENTAL,
                                    required=False,
                                    help_text="For display purposes only. Most Abilities may be used for physical or "
                                              "mental actions, depending on the situation.")

    def __init__(self, *args, **kwargs):
        super(AbilityForm, self).__init__(*args, **kwargs)
        if 'ability' in self.initial:
            ability = self.initial["ability"]
            self.initial["ability_name"] = ability.name
            self.initial["ability_is_primary"] = ability.is_primary
            self.initial["ability_tutorial_text"] = ability.tutorial_text
            self.initial["phys_mental"] = PHYS_MENTAL[0] if ability.is_physical else PHYS_MENTAL[1]

            self.fields['name'].initial = ability.name
            self.fields['ability_id'].initial = ability.id
            self.fields['description'].widget = forms.HiddenInput()
            self.fields['name'].widget = forms.HiddenInput()
        if 'value_id' in self.initial and self.initial['value_id']:
            self.fields['value_id'].initial = self.initial['value_id']

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

class BattleScarForm(forms.Form):
    description = forms.CharField(max_length=900,
                                  label=None,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
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

def make_charon_coin_form(character=None):
    initial = character.assigned_coin() if character else False
    class CharonCoinForm(forms.Form):
        spend_coin = forms.BooleanField(required=False,
                                        initial=initial)
    return CharonCoinForm

class DeleteCharacterForm(forms.Form):
    pass