from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator


def make_consumable_crafting_form(power_full):
    class ConsumableCraftingForm(forms.Form):
        power_full_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=True, initial=power_full.pk)
        num_crafted = forms.IntegerField(label="Number Crafted",
                                         validators=[MinValueValidator(0), MaxValueValidator(20)],
                                         widget=forms.NumberInput(attrs={
                                             'class': 'consumable-value-input form-control',
                                             'v-model': 'consumableQuantities[{}]'.format(power_full.pk),
                                         }))
    return ConsumableCraftingForm


def make_artifact_crafting_form(character):
    artifact_choices = character.artifact_set.filter(cell__isnull=True,
                                                     is_signature=False,
                                                     is_consumable=False,
                                                     crafting_character=character).all()

    class ArtifactCraftingForm(forms.Form):
        power_full_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=True)
        artifact_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=True)
        artifact = forms.ModelChoiceField(queryset=artifact_choices,
                                      empty_label="Create new Artifact",
                                      required=False,)
        new_art_name = forms.CharField(max_length=300,
                               required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
        new_art_description = forms.CharField(max_length=1000,
                                       required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control'}))
        refund = forms.BooleanField(label="Refund",
                                    required=False,
                                    help_text="Refund this crafting?")
        upgrade = forms.BooleanField(label="Refund",
                                     required=False,
                                     initial=True,
                                     help_text="Upgrade this Artifact?")

    return ArtifactCraftingForm
