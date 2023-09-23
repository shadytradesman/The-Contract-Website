from django import forms

from tinymce.widgets import TinyMCE


class AnswerForm(forms.Form):
    content = forms.CharField(label='',
                              widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                              max_length=73000,
                              required=False)