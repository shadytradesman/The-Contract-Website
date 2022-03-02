from django import forms
from .models import Enhancement, Drawback, Power_Full, PowerTag, Base_Power, EFFECT, MODALITY, VECTOR
from characters.models import Weapon


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
    description = forms.CharField(label='Description',
                                  widget=forms.Textarea(attrs={
                                     "v-model": "giftDescription",
                                  }),
                                  max_length=2500,
                                  required=True,
                                  help_text="Describe what the Gift looks like when it is used, how it works, "
                                            "and its impact on the owner, target, and environment.")

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
                                        'v-bind:value': 'selectedVector',
                                    }))


class ModifierForm(forms.Form):
    # input fields
    details = forms.CharField(required=False, max_length=1200)
    is_selected = forms.BooleanField(required=False)

    # metadata fields
    mod_slug = forms.CharField(label=None, widget=forms.HiddenInput(attrs={
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
    # input fields
    ability_choice = forms.CharField(required=False, max_length=500)
    attribute_choice = forms.CharField(required=False, max_length=500)

