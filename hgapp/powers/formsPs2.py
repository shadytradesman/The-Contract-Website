from django import forms
from django.forms import formset_factory

from .models import PowerTag, Base_Power, EFFECT, MODALITY, VECTOR, CRAFTING_SIGNATURE
from characters.models import Weapon, Artifact
from hgapp.utilities import get_object_or_none


class PowerForm(forms.Form):
    name = forms.CharField(label='Gift Name',
                           max_length=100,
                           required=True,
                           widget=forms.TextInput(attrs={
                                "v-model": "giftName",
                                "@input": "changeParam",
                           }))
    tagline = forms.CharField(label='Tagline',
                              max_length=2000,
                              required=False,
                              help_text="(Optional) Introduce the Gift in a flavorful way.",
                              widget=forms.TextInput(attrs={
                                  "v-model": "giftTagline",
                              }))
    description = forms.CharField(label='Visual Description',
                                  widget=forms.Textarea(attrs={
                                     "v-model": "giftDescription",
                                     "class": "form-control",
                                  }),
                                  max_length=2000,
                                  required=True,
                                  help_text="A concise description of what this Gift looks like when it is "
                                            "used. What do participants and observers experience? This will be "
                                            "referenced by GMs at game-time to help them narrate.")
    extended_description = forms.CharField(label='Extended Description',
                                  widget=forms.Textarea(attrs={
                                      "v-model": "giftExtendedDescription",
                                      "class": "form-control",
                                  }),
                                  max_length=8000,
                                  required=False,
                                  help_text="(Optional) Wax poetic about this Gift's background, metaphysics, etc.")

    # admin only fields
    tags = forms.ModelMultipleChoiceField(queryset=PowerTag.objects.order_by("tag").all(),
                                          required=False,
                                          widget=forms.CheckboxSelectMultiple)
    example_description = forms.CharField(label='Example Description',
                                          widget=forms.Textarea,
                                          required=False,
                                          help_text='Admin only, optional, for the stock powers page. Follow-up advice for this power. '
                                                    'What sorts of Enhancements and Drawbacks would be good?')
    stock_order = forms.IntegerField(label="Stock Gift ordering",
                                     required=False,
                                     initial=0,
                                     help_text="Determines the order in the stock Gifts page. Higher numbers appear first.")

    # Hidden Fields
    modality = forms.ModelChoiceField(queryset=Base_Power.objects.filter(base_type=MODALITY).all(),
                                      required=True,
                                      widget=forms.HiddenInput(attrs={
                                          'v-bind:value': 'selectedModality.slug',
                                      }))
    effect = forms.ModelChoiceField(queryset=Base_Power.objects.filter(base_type=EFFECT).all(),
                                    required=True,
                                    widget=forms.HiddenInput(attrs={
                                        'v-bind:value': 'selectedEffect.slug',
                                    }))
    vector = forms.ModelChoiceField(queryset=Base_Power.objects.filter(base_type=VECTOR).all(),
                                    required=True,
                                    widget=forms.HiddenInput(attrs={
                                        'v-bind:value': 'selectedVector.slug',
                                    }))


def make_select_signature_artifact_form(existing_character=None, existing_power=None, user=None):
    initial_artifact_queryset = Artifact.objects.none()
    initial_artifact = None
    if existing_power and existing_power.crafting_type == CRAFTING_SIGNATURE:
        initial_artifact = get_object_or_none(existing_power.artifactpowerfull_set.filter(relevant_artifact__is_signature=True))
        initial_artifact_queryset = Artifact.objects.filter(pk=initial_artifact.relevant_artifact.pk)
    if existing_character:
        queryset = existing_character.artifact_set.filter(
            cell__isnull=True,
            crafting_character=existing_character,
            is_signature=True)
    elif existing_power and existing_power.owner == user:
        queryset = Artifact.objects.filter(
            creating_player=existing_power.owner,
            cell__isnull=True,
            crafting_character__isnull=True,
            is_signature=True)
    elif user and user.is_authenticated:
        queryset = Artifact.objects.filter(
            creating_player=user,
            cell__isnull=True,
            crafting_character__isnull=True,
            is_signature=True)
    else:
        queryset = Artifact.objects.none()
    final_queryset = initial_artifact_queryset | queryset

    class SelectArtifactForm(forms.Form):
        selected_artifact = forms.ModelChoiceField(queryset=final_queryset,
                                                   initial=initial_artifact,
                                                   required=False,
                                                   empty_label="Create New Artifact",
                                                   label="Attach to existing Legendary Artifact?",
                                                   widget=forms.Select(attrs={
                                                       'v-model': 'selectedItem',
                                                       "@input": "changeSelectedItem",
                                                   }))
        item_name = forms.CharField(required=False,
                                    max_length=450,
                                    help_text="The name of the Legendary Artifact",
                                    widget=forms.TextInput(attrs={
                                        'v-model': 'sigItemName',
                                    }))
        item_description = forms.CharField(required=False,
                                           max_length=5000,
                                           help_text="(Optional) A physical description of the Artifact",
                                           widget=forms.TextInput(attrs={
                                               'v-model': 'sigItemDescription',
                                           }))

    return SelectArtifactForm


class ModifierForm(forms.Form):
    # input fields
    details = forms.CharField(required=False, max_length=1200, widget=forms.HiddenInput(attrs={
        'v-bind:value': 'modifier.details',
        "autocorrect": "off",
        "autocapitalize": "none",
        "autocomplete": "off",
    }),)
    is_selected = forms.BooleanField(required=False, label=None, widget=forms.HiddenInput(attrs={
        'v-bind:checked': '(modifier.isEnhancement?selectedEnhancements:selectedDrawbacks).map(enh => enh.id).includes(modifier.id)',
        'v-bind:value': '(modifier.isEnhancement?selectedEnhancements:selectedDrawbacks).map(enh => enh.id).includes(modifier.id)',
    }),)
    # This field is an admin-only field to mark which modifiers are advancement recs for stock gifts
    is_advancement = forms.BooleanField(required=False, label=None, widget=forms.HiddenInput(attrs={
        'v-bind:checked': '(modifier.isEnhancement?advancementEnhancements:advancementDrawbacks).map(enh => enh.id).includes(modifier.id)',
        'v-bind:value': '(modifier.isEnhancement?advancementEnhancements:advancementDrawbacks).map(enh => enh.id).includes(modifier.id)',
    }),)
    # metadata fields
    mod_slug = forms.CharField(required=True, label=None, widget=forms.HiddenInput(attrs={
        'v-bind:value': 'modifier.slug',
      }),) # slug for the Enhancement or Drawback
    is_enhancement = forms.BooleanField(required=False, label=None, widget=forms.HiddenInput(attrs={
        'v-bind:value': 'modifier.isEnhancement',
    }),) # if False, this modifier is a Drawback

    def clean_details(self):
        data = self.cleaned_data['details']
        return clean_user_input_field(data)


class ParameterForm(forms.Form):
    level = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'v-bind:value': 'selectedLevelOfParam(param)',
            'v-bind:disabled': 'param.id in this.disabledParameters',
        }), )
    power_param_id = forms.IntegerField(
        label=None,
        widget=forms.HiddenInput(attrs={
            'v-bind:value': 'param.powParamId',
        }),)


class SystemField(forms.Form):
    field_id = forms.IntegerField(label=None,
                                  widget=forms.HiddenInput(attrs={
                                      'v-bind:value': 'field.pk',
                                  }),)


class SystemFieldTextForm(SystemField):
    detail_text = forms.CharField(required=True,
                                  max_length=500,
                                  label="",
                                  widget=forms.TextInput(attrs={
                                      "v-model": "fieldTextInput[field.id]",
                                      "class": "form-control",
                                      "@input": "changeParam",
                                      "autocorrect": "off",
                                      "autocapitalize": "none",
                                      "autocomplete": "off",
                                  }))

    def clean_details_text(self):
        data = self.cleaned_data['details_text']
        return clean_user_input_field(data)


class SystemFieldWeaponForm(SystemField):
    weapon_choice = forms.ModelChoiceField(queryset=Weapon.objects.all(),
                                           required=True,
                                           widget=forms.HiddenInput(attrs={
                                               'v-bind:value': 'fieldWeaponInput[field.id]',
                                           }))


class SystemFieldRollForm(SystemField):
    attribute_roll = forms.CharField(required=True,
                                     max_length=500,
                                     label="",
                                     widget=forms.HiddenInput(attrs={
                                         "v-model": "fieldRollInput[field.id][0][0]",
                                     }))
    ability_roll = forms.CharField(required=False,
                                   max_length=500,
                                   label="",
                                   widget=forms.HiddenInput(attrs={
                                       "v-if": "field.abilityChoices.length > 0",
                                       "v-model": "fieldRollInput[field.id][1][0]",
                                   }))


def get_params_formset(POST=None):
    return formset_factory(ParameterForm, extra=0)(POST, prefix="parameters")


def get_modifiers_formset(POST=None):
    return formset_factory(ModifierForm, extra=0)(POST, prefix="modifiers")


def get_sys_field_text_formset(POST=None):
    return formset_factory(SystemFieldTextForm, extra=0)(POST, prefix="sys_field_text")


def get_sys_field_weapon_formset(POST=None):
    return formset_factory(SystemFieldWeaponForm, extra=0)(POST, prefix="sys_field_weapon")


def get_sys_field_roll_formset(POST=None):
    return formset_factory(SystemFieldRollForm, extra=0)(POST, prefix="sys_field_roll")


html_replace_map = {
    '(': '&#40;',
    ')': '&#41;',
    '[': '&#91;',
    ']': '&#93;',
    '&': '&#38;',
    '%': '&#37;',
    '|': '&#124;',
    '{': '&#123;',
    '}': '&#125;',
    '$': '&#36;',
    '+': '&#43;',
    '#': '&#35;',
    ';': '&#59;',
    '!': '&#33;',
    '*': '&#42;',
}

def clean_user_input_field(user_input):
    # We do this so the user can't mess up system text rendering.
    output = ""
    for char in user_input:
        if char in html_replace_map:
            output += html_replace_map[char]
        else:
            output += char
    return output

