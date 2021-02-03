from django import forms

from overrides.widgets import CustomStylePagedown



class EditProfileForm(forms.Form):
    about = forms.CharField(label='About',
                            max_length=1000,
                            widget=CustomStylePagedown(),)

class AcceptTermsForm(forms.Form):
    pass