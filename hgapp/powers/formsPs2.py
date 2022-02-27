from django import forms
from .models import Enhancement, Drawback, Power_Full, PowerTag, Base_Power, EFFECT, MODALITY, VECTOR


class PowerForm(forms.Form):
    name = forms.CharField(label='Power Name', max_length=100)
    flavor = forms.CharField(label='Put a ribbon on it',
                             help_text='A snippet of text that introduces the Power in a flavorful way',
                             max_length=100)
    description = forms.CharField(label='Description',
                                  widget=forms.Textarea,
                                  max_length=2500)
    modality = forms.ModelChoiceField(queryset=Base_Power.objects.filter(base_type=MODALITY).all(), required=True,)
    effect = forms.ModelChoiceField(queryset=Base_Power.objects.filter(base_type=EFFECT).all(), required=True,)
    vector = forms.ModelChoiceField(queryset=Base_Power.objects.filter(base_type=VECTOR).all(), required=True,)

    # admin only fields
    tags = forms.ModelMultipleChoiceField(queryset=PowerTag.objects.order_by("tag").all(),
                                          required=False,
                                          widget=forms.CheckboxSelectMultiple)
    example_description = forms.CharField(label='Example Description',
                                          widget=forms.Textarea,
                                          required=False,
                                          help_text='Admin only, optional, for the stock powers page. Follow-up advice for this power. '
                                                    'What sorts of Enhancements and Drawbacks would be good?')


# The forms below are not rendered in the FE but are populated by vue and passed to the backend for validation and
# cleaning. Their initial values are populated, so the BE can tell if a field has changed.


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
    # input fields
    level = forms.IntegerField(required=True)
    # metadata fields
    power_param_id = forms.IntegerField(label=None, widget=forms.HiddenInput(),)


class SystemFieldTextForm(forms.Form):
    # input fields
    detail_text = forms.CharField(required=False, max_length=500)

    # metadata fields
    field_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), )


class SystemFieldRollForm(forms.Form):
    # input fields
    ability_choice = forms.CharField(required=False, max_length=500)
    attribute_choice = forms.CharField(required=False, max_length=500)

    # metadata fields
    field_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), )


class SystemFieldWeaponForm(forms.Form):
    # input fields
    weapon_choice = forms.CharField(required=False, max_length=500)

    # metadata fields
    field_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), )