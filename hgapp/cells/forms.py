from django import forms
from tinymce.widgets import TinyMCE

from overrides.widgets import CustomStylePagedown
from .models import ROLE

class EditCellForm:
    pass

class EditWorldForm(forms.Form):
    name = forms.CharField(label='Name',
                                   max_length=195,
                                   widget=forms.TextInput(attrs={'class': 'form-control'}),
                                   help_text='The name of your World. For example, \"Earth, 1989\" or \"Feudal Japan.\"')
    setting_sheet_blurb = forms.CharField(label='Character Sheet Setting Summary',
                                          max_length=500,
                                          required=False,
                                          widget=forms.TextInput(attrs={'class': 'form-control'}),
                                          help_text= '"much like our own. . .", "where it\'s still the eighties. . .", "where dinosaurs rule. . ." '
                                                     ' Appears on the Character Sheets for Contractors who call this Setting home.')
    setting_description = forms.CharField(label='',
                                          widget=TinyMCE(attrs={'cols': 70, 'rows': 10}),
                                          max_length=68000,
                                          required=False,
                                          help_text='')
    house_rules = forms.CharField(label='House Rules',
                                  widget=TinyMCE(attrs={'cols': 70, 'rows': 10}),
                                  max_length=48000,
                                  required=False,
                                  help_text='Rules that exist only in this World.')
    are_contractors_portable = forms.BooleanField(label='Contractors are Portable',
                                                  required=False,
                                                  help_text='Check this box to allow Contractors to participate in Games in other Worlds. '
                                                            'If your House Rules affect Gifts, Experience, or Powers, uncheck this box.')
    setting_create_char_info = forms.CharField(label='',
                                               widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                                               max_length=9800,
                                               required=False,
                                               help_text='')
    setting_summary = forms.CharField(label='World Summary',
                                                 widget=forms.Textarea(),
                                                 max_length=9500,
                                                 required=False,
                                                 help_text='A brief overview / introduction for this World\'s Setting, used '
                                                           'throughout the site.')


class CustomInviteForm(forms.Form):
    username = forms.CharField(label=None,
                            max_length=200)
    invite_text = forms.CharField(label='Message',
                            max_length=800,
                            widget=forms.Textarea,
                            help_text='Any extra information to send with the invite',
                            required=False)


class RecruitmentForm(forms.Form):
    list_publicly = forms.BooleanField(label='List Publicly',
                                       required=False,
                                       help_text='If checked, your Cell will appear on the "Looking for Cell" page.')
    allow_self_invites = forms.BooleanField(label='Allow Self-Invites',
                                            required=False,
                                            help_text='If checked, anyone with an account may join your Cell.')
    cell_sell = forms.CharField(label='Cell Sell',
                                widget=forms.Textarea,
                                max_length=9800,
                                required=False,
                                help_text='Summarize your Cell (not setting) to prospective Players.')
    community_link = forms.CharField(label='Community Link',
                                     max_length=1000,
                                     required=False,
                                     help_text='Link to a forum, Discord Server, or other site where this Cell hangs out.')


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
                             widget=forms.Select(attrs={'form': 'manage_form', 'class': 'form-control form-inline'}))