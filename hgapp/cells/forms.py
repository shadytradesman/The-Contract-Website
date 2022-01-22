from django import forms
from django.forms import ModelForm
from tinymce.widgets import TinyMCE

from .models import ROLE, WebHook


class EditWorldForm(forms.Form):
    name = forms.CharField(label='Name',
                           max_length=195,
                           widget=forms.TextInput(attrs={'class': 'form-control'}),
                           help_text='The name of your Playgroup. For example, \"Costa College Contractors\"')
    setting_name = forms.CharField(label='Setting Name',
                                   max_length=195,
                                   widget=forms.TextInput(attrs={'class': 'form-control'}),
                                   help_text='The name of your Playgroup\'s Setting. For example, \"Earth, 1989\" or \"Feudal Japan.\"')
    setting_sheet_blurb = forms.CharField(label='Character Sheet Setting Blurb',
                                          max_length=500,
                                          required=False,
                                          widget=forms.TextInput(attrs={'class': 'form-control'}),
                                          help_text= '"in the California Bay Area. . .", "where it\'s still the eighties. . .", "where dinosaurs rule. . ." '
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
                                  help_text='Rules that exist only in this Playgroup.')
    use_golden_ratio = forms.BooleanField(label='Enable Golden Ratio',
                                                  required=False,
                                                  help_text='If this box is checked, GMs who run Contracts in this '
                                                            'Playgroup will receive an Improvement if they run a '
                                                            'Contract where at least one Contractor dies while another '
                                                            'achieves Victory. Note: GMs cannot receive both a Golden '
                                                            'Ratio and "Gm for a brand New Player" Improvement from the '
                                                            'same Contract.')
    are_contractors_portable = forms.BooleanField(label='Contractors are Portable',
                                                  required=False,
                                                  help_text='Check this box to allow Contractors to participate in Contracts in other Playgroups. '
                                                            'If your House Rules affect Gifts, Experience, or Powers, uncheck this box.')
    setting_create_char_info = forms.CharField(label='',
                                               widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                                               max_length=9800,
                                               required=False,
                                               help_text='')
    setting_summary = forms.CharField(label='Setting Summary',
                                                 widget=forms.Textarea(),
                                                 max_length=9500,
                                                 required=False,
                                                 help_text='A brief overview / introduction for this Playgroup\'s Setting, used '
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
                                       help_text='If you check this box and provide a link to a community below, your Playgroup will appear on the "Find Playgroups" page.')
    allow_self_invites = forms.BooleanField(label='Open Memberships',
                                            required=False,
                                            help_text='If checked, anyone with an account may join your Playgroup. '
                                                      'Otherwise, they must use an invite link or a Playgroup member with '
                                                      '"manage memberships" permissions must invite them.')
    cell_sell = forms.CharField(label='Playgroup Sell',
                                widget=forms.Textarea,
                                max_length=1500,
                                required=False,
                                help_text='Summarize your Playgroup to prospective Players. What is the setting? What kinds of '
                                          'Players should join? How can they join you and start playing?')
    community_link = forms.URLField(label='Community Link',
                                     max_length=1000,
                                     required=False,
                                     help_text='Link to a forum, Discord Server, or other site where the members of this Playgroup hang out. '
                                               '<b>You must fill this field for your Playgroup to appear on the "Find a Playgroup" list.</b> '
                                               '<i>Note: If you use a Discord invite link, ensure it is set to never expire.</i>')
    is_community_link_public = forms.BooleanField(label='Show Community Link to Non-Members',
                                                  required=False,
                                                  initial=True,
                                                  help_text='If checked, your Playgroup\'s Community Link will be visible to non-members.' )


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

class RolePermissionForm(forms.Form):
    # attrs must be set to allow forms with other submit target urls to exist within other forms in template.
    role = forms.CharField(label=None,
                                max_length=200,
                                widget=forms.HiddenInput())
    can_manage_memberships = forms.BooleanField(required=False)
    can_gm_games = forms.BooleanField(required=False)
    can_post_events = forms.BooleanField(required=False)
    can_manage_member_characters = forms.BooleanField(required=False)
    can_edit_world = forms.BooleanField(required=False)
    can_manage_games = forms.BooleanField(required=False)

class EditWorldEventForm(forms.Form):
    headline = forms.CharField(label='Headline',
                           max_length=900,
                           help_text='',
                               required=False)
    event_description = forms.CharField(label='Content',
                                          widget=TinyMCE(attrs={'cols': 70, 'rows': 10}),
                                          max_length=49000,
                                          required=False,
                                          help_text='')
    should_delete = forms.BooleanField(label='Delete Event',
                                       initial=False,
                                       required=False,
                                       help_text='If checked, this World Event will be deleted.')
