from django import forms
from django.forms import ModelChoiceField
from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import datetime

from overrides.widgets import CustomStylePagedown
from .models import ROLE

class CreateCellForm(forms.Form):
    name = forms.CharField(label='Name',
                           max_length=195,
                           help_text='The name of your Cell. Examples: \"Sierra College Games Group\" or \"Circe\'s Coven\"')
    setting_name = forms.CharField(label='Setting Name',
                           max_length=195,
                           help_text='The name of your Cell\'s primary setting. Examples: \"Earth, 1989\" or \"Feudal Japan\"')
    setting_description = forms.CharField(label='Setting Description',
                            widget=CustomStylePagedown(),
                            max_length=39990,
                            help_text='A description of the setting. Each Cell has its own private world, so it can be '
                                      'anything you\'d like. It\'s helpful to explain the time period, available tech, '
                                      'prevalence of supernatural elements, etc')

class CustomInviteForm(forms.Form):
    username = forms.CharField(label=None,
                            max_length=200)
    invite_text = forms.CharField(label='Message',
                            max_length=800,
                            widget=forms.Textarea,
                            help_text='Any extra information to send with the invite',
                            required=False)

class RsvpForm(forms.Form):
    pass

class KickForm(forms.Form):
    pass

class PlayerRoleForm(forms.Form):
    # attrs must be set to allow forms with other submit target urls to exist within other forms in template.
    player_id = forms.CharField(label=None,
                            max_length=200,
                            widget=forms.TextInput(attrs={'form': 'manage_form'}))
    role = forms.ChoiceField(choices=ROLE,
                             widget=forms.Select(attrs={'form': 'manage_form'}))