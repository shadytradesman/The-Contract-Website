from django import forms

from tinymce.widgets import TinyMCE

class JournalForm(forms.Form):
    title = forms.CharField(label='Journal Title',
                            required=False,
                            max_length=380)
    content = forms.CharField(label='Journal Body',
                                  widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                                  max_length=93000,
                                  required=False,
                                  help_text='Write in-character. You must write at least 250 words for a Contract journal and 150 words for a Downtime journal to receive rewards.')
    contains_spoilers = forms.BooleanField(label="Contains Spoilers",
                                       required=False,
                                       help_text="Select if this journal contains spoilers for the Scenario.")
    is_nsfw = forms.BooleanField(label="Contains 18+ Content",
                                 required=False,
                                 help_text="Select if this journal contains content unsuitable for those under the age of 18.")


class JournalCoverForm(forms.Form):
    title = forms.CharField(label='Journal Cover Title',
                            max_length=380)
    content = forms.CharField(label='Journal Cover',
                              widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
                              max_length=73000,
                              required=False,
                              help_text='Describe the journal itself, provide an in-character forward, or customize as you see fit.')
