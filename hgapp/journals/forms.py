from django import forms
from django.forms import ModelChoiceField
from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import datetime
from account.conf import settings
from django.utils import timezone

from tinymce.widgets import TinyMCE

class JournalForm(forms.Form):
    title = forms.CharField(label='Journal Title',
                            required=False,
                            max_length=380)
    content = forms.CharField(label='Journal Body',
                                  widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                                  max_length=73000,
                                  required=False,
                                  help_text='Write in-character. You must write at least 250 words to recieve rewards.')
    contains_spoilers = forms.BooleanField(label = "Contains Spoilers",
                                       required=False,
                                       help_text = "This journal contains spoilers for the Scenario")


class JournalCoverForm(forms.Form):
    title = forms.CharField(label='Journal Cover Title',
                            max_length=380)
    content = forms.CharField(label='Journal Cover',
                              widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                              max_length=73000,
                              required=False,
                              help_text='Describe the journal itself, provide an in-character forward, or customize as you see fit.')
