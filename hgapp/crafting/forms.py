from django import forms
from django.core.validators import MinValueValidator


class ConsumableCraftingForm(forms.Form):
    power_full_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=True)
    num_crafted = forms.IntegerField(label="Number Crafted",
                                     validators=[MinValueValidator(0)])


class ArtifactCraftingForm(forms.Form):
    power_full_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=True)
    artifact_id = forms.IntegerField(label=None, widget=forms.HiddenInput(), required=True)
    refund = forms.BooleanField(label="Refund",
                                required=False,
                                help_text="Refund this crafting?")
    upgrade = forms.BooleanField(label="Refund",
                                 required=False,
                                 initial=True,
                                 help_text="Upgrade this Artifact?")
