from django import forms
from django.forms import formset_factory

from .models import PowerTag, Base_Power, EFFECT, MODALITY, VECTOR
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
                              max_length=100,
                              required=False,
                              widget=forms.TextInput(attrs={
                                  "v-model": "giftTagline",
                              }))
    description = forms.CharField(label='Visual Description',
                                  widget=forms.Textarea(attrs={
                                     "v-model": "giftDescription",
                                  }),
                                  max_length=2000,
                                  required=True,
                                  help_text="Describe what this Gift looks like when it is used "
                                            "and its impact on the owner, target, and environment.")
    extended_description = forms.CharField(label='Extended Description',
                                  widget=forms.Textarea(attrs={
                                      "v-model": "giftExtendedDescription",
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


def make_select_signature_artifact_form(existing_character=None, existing_power=None):
    class SelectArtifactForm(forms.Form):
        initial_artifact = None
        if existing_character:
            queryset = existing_character.artifact_set.filter(
                cell__isnull=True,
                crafting_character=existing_character,
                is_signature=True)
            if existing_power and hasattr(existing_power, "artifacts_set"):
                initial_artifact = get_object_or_none(existing_power.artifacts_set.filter(is_signature=True))
        else:
            queryset = Artifact.objects.none()
            initial_artifact = None
        selected_artifact = forms.ModelChoiceField(queryset=queryset,
                                                   initial=initial_artifact,
                                                   required=False,
                                                   empty_label="Create New Item",
                                                   label="Add to existing Signature Item?")
        item_name = forms.CharField(required=True,
                                    max_length=450,
                                    help_text="The name of the signature item")
        item_description = forms.CharField(required=True,
                                           max_length=5000,
                                           help_text="A physical description of the signature item")
    return SelectArtifactForm


class ModifierForm(forms.Form):
    # input fields
    details = forms.CharField(required=False, max_length=1200)
    is_selected = forms.BooleanField(required=False)

    # metadata fields
    mod_slug = forms.CharField(required=True, label=None, widget=forms.HiddenInput(attrs={
        'v-bind:value': 'modifier.slug',
      }),) # slug for the Enhancement or Drawback
    is_enhancement = forms.BooleanField(required=False, label=None, widget=forms.HiddenInput(attrs={
        'v-bind:value': 'modifier.isEnhancement',
    }),) # if False, this modifier is a Drawback


class ParameterForm(forms.Form):
    level = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput(attrs={
            'v-bind:value': 'selectedLevelOfParam(param)',

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
                                  }))


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
