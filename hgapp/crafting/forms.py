from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from powers.models import CRAFTING_ARTIFACT


def make_consumable_crafting_form(power_full):
    class ConsumableCraftingForm(forms.Form):
        power_full_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=True, initial=power_full.pk)
        num_crafted = forms.IntegerField(label="Number Crafted",
                                         validators=[MinValueValidator(0), MaxValueValidator(20)],
                                         widget=forms.NumberInput(attrs={
                                             'class': 'consumable-value-input form-control',
                                             '@change': 'recalculateExpCosts',
                                             'v-model': 'consumableQuantities[{}]'.format(power_full.pk),
                                         }))
    return ConsumableCraftingForm


class NewArtifactForm(forms.Form):
    name = forms.CharField(max_length=300,
                                   required=True,
                                   widget=forms.TextInput(attrs={
                                       'class': 'form-control',
                                       'v-model': 'artifact.name',
                                       'required': '',
                                   }))
    description = forms.CharField(max_length=1000,
                                          required=True,
                                          widget=forms.TextInput(attrs={
                                              'class': 'form-control',
                                              'v-model': 'artifact.description',
                                              'required': '',
                                          }))
    # negative number for new artifact
    artifact_id = forms.IntegerField(label=None, widget=forms.HiddenInput(attrs={
            'v-model': 'artifact.id'
        }), required=True)


def make_artifact_gift_selector_form(character):
    queryset = character.power_full_set.filter(crafting_type=CRAFTING_ARTIFACT).all()

    class ArtifactCraftingForm(forms.Form):
        selected_gifts = forms.ModelMultipleChoiceField(queryset=queryset, widget=forms.CheckboxSelectMultiple(), required=False)
        # negative number for new artifact
        artifact_id = forms.IntegerField(label=None, widget=forms.HiddenInput(attrs={
                'v-model': 'artifact.id'
            }), required=True)

    return ArtifactCraftingForm
