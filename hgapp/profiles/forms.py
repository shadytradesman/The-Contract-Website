from django import forms

from overrides.widgets import CustomStylePagedown


class EditProfileForm(forms.Form):
    about = forms.CharField(label='About',
                            max_length=10000,
                            widget=CustomStylePagedown(),)