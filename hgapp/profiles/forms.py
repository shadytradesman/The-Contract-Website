from django import forms

from overrides.widgets import CustomStylePagedown



class EditProfileForm(forms.Form):
    about = forms.CharField(label='About',
                            max_length=1000,
                            required=False,
                            widget=CustomStylePagedown(),)

    view_adult = forms.BooleanField(label="View Adult Content",
                                    required=False,
                                    help_text="By selecting this box, you certify that you are age 18 or older and wish "
                                              "to view content marked as adult.")

class AcceptTermsForm(forms.Form):
    pass