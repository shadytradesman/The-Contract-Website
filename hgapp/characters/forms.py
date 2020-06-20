from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from overrides.widgets import CustomStylePagedown

from characters.models import Character, BasicStats, Character_Death

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
        ('1', '1 - Dumb'),
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

def make_character_form(user):
    class CharacterForm(ModelForm):
        class Meta:
            model = Character
            fields = ('name', 'private', 'tagline', 'appearance', 'age', 'sex', 'concept_summary', 'ambition', 'paradigm',
                      'residence', 'languages', 'insanities', 'disabilities', 'current_alias', 'previous_aliases',
                      'resources', 'contacts', 'equipment', 'total_encumbrance', 'max_encumbrance', 'wish_list',
                      'to_do_list', 'contracts', 'background', 'notes')
            help_texts = {
                'name': _('The Character\'s Name'),
                'private': _("If checked, character will not be publicly viewable."),
                'tagline': _('A subtitle that introduces the character in a flavorful way'),
                'appearance': _('A brief description of the character\'s outward appearance'),
                'concept_summary': _('A very brief overview of the primary concept, themes, and archetypes'),
                'ambition': _('Why does this character risk their lives and participate in the games?'),
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
                'equipment': CustomStylePagedown(),
                'notes': CustomStylePagedown(),
                'appearance': forms.TextInput(),
            }

    form = CharacterForm
    queryset = user.cell_set.all()
    cell = forms.ModelChoiceField(queryset=queryset,
                                  empty_label="Free Agent (No Cell)",
                                  help_text="Select a Cell for your character. "
                                            "This defines your character's home world and allows "
                                            "Cell leaders to help you with record-keeping. "
                                            "NOTE: Cell leaders will be able to view and edit your character.",
                                  required=False)
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
    value = forms.ChoiceField(choices=(()))
    attribute_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),) # hidden field to track which attribute we are editing.

    def __init__(self, *args, **kwargs):
        super(AttributeForm, self).__init__(*args, **kwargs)
        attribute = self.initial["attribute"]
        self.fields['value'].label = attribute.name
        if attribute.name in ATTRIBUTE_VALUES:
            self.fields['value'].choices = ATTRIBUTE_VALUES[attribute.name]
        else:
            self.fields['value'].choices = ATTRIBUTE_VALUES["default"]

class AbilityForm(forms.Form):
    ability_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),) # hidden field to track which abilities we are editing.
    value = forms.IntegerField(initial=0,
                               validators=[MaxValueValidator(5), MinValueValidator(0)],
                               widget=forms.NumberInput(attrs={'class': 'ability-value-input form-control'}))
    name = forms.CharField(max_length=50,
                           widget=forms.TextInput(attrs={'class': 'form-control sec-ability-name'}))
    description = forms.CharField(max_length=250,
                                  widget=forms.TextInput(attrs={'class': 'form-control sec-ability-desc'}))

    def __init__(self, *args, **kwargs):
        super(AbilityForm, self).__init__(*args, **kwargs)
        if 'ability' in self.initial:
            ability = self.initial["ability"]
            self.fields['name'].initial = ability.name
            self.fields['ability_id'].initial = ability.id
            self.fields['description'].widget = forms.HiddenInput()
            self.fields['name'].widget = forms.HiddenInput()

class QuirkForm(forms.Form):
    id = forms.IntegerField(label=None, widget=forms.HiddenInput(),) # hidden field to track which quirks we are editing.
    is_selected = forms.BooleanField()
    details = forms.CharField(max_length=600,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(QuirkForm, self).__init__(*args, **kwargs)
        if 'quirk' in self.initial:
            quirk = self.initial["quirk"]
            self.fields['id'].initial = quirk.id
            self.fields['is_selected'].label = quirk.name
            self.fields['is_selected'].widget = forms.CheckboxInput(attrs={'class': 'quirk-multiple-' + str(quirk.multiplicity_allowed)})

class LiabilityForm(QuirkForm):
    pass

class AssetForm(QuirkForm):
    pass