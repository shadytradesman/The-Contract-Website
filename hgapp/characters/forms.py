from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from overrides.widgets import CustomStylePagedown

from characters.models import Character, BasicStats, Character_Death

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
                'concept': _('A very brief overview of the primary concept, themes, and archetypes'),
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

class BasicStatsForm(ModelForm):
    class Meta:
        model = BasicStats
        fields = ('stats', 'advancement_history', 'movement', 'armor')
        help_texts = {
            'stats': _('Attributes, skills, etc'),
            'advancement_history':  _('History of experience, skillpoints, or similar'),
            'movement': _('Information about how quickly the character can move, climb, swim'),
            'armor': _('Armor rating (if applicable)')
        }
        widgets = {
            'stats': CustomStylePagedown(),
            'advancement_history': CustomStylePagedown(),
        }

    hg15_stats_template = """Attributes
----------
**Strength**: 1
**Dexterity**: 1
**Stamina**:  1
**Charisma**: 1
**Perception**: 1
**Intelligence**: 1
**Wits**: 1

Abilities
---------
**Academics**: 
**Alertness**: 
**Animal Ken**: 
**Athletics**: 
**Brawl**: 
**Computer**: 
**Crafts**: 
**Dodge**: 
**Endurance**: 
**Firearms**: 
**Investigation**: 
**Legerdemain**: 
**Linguistics**: 
**Medicine**: 
**Meditation**: 
**Melee**: 
**Occult**: 
**Performance**: 
**Pilot**: 
**Science**: 
**Stealth**: 
**Survival**: 

Merits
------
none

Flaws
-----
none

Traumas
-------
**Murder:** Kill a human for any reason other than immediate self defense.
**Humanity:** Witnessing a humanitarian atrocity (torture, massacre, mutilation, rape)
**Torture:** Being tortured (solitary confinement for an extended period, physical torture)

Pools
-----

**Willpower:** 1"""

