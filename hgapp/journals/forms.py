from django import forms
from django.forms import ModelChoiceField
from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import datetime
from account.conf import settings
from django.utils import timezone

from tinymce.widgets import TinyMCE

class JournalForm(forms.Form):
    title = forms.CharField(label='Journal Title',
                            max_length=380)
    content = forms.CharField(label='Journal Body',
                                  widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                                  max_length=73000,
                                  help_text='Write in-character. You must write at least 250 words to recieve rewards.')
    contains_spoilers = forms.BooleanField(label = "Downtime",
                                       required=False,
                                       help_text = "This Journal describes the events occurring after the Game rather than the Game itself.")
