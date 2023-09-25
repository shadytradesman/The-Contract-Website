from django import forms

from tinymce.widgets import TinyMCE


class AnswerForm(forms.Form):
    content = forms.CharField(label='',
                              widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                              max_length=73000,
                              required=False)
    is_nsfw = forms.BooleanField(label="Contains 18+ Content",
                                 required=False,
                                 help_text="Select if this answer contains content unsuitable for those under the age of 18.")
