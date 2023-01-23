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
                                              "to view content marked as adult. Lying about your age is a bannable offense.")
    private_profile = forms.BooleanField(
        label="Profile is private",
        required=False,
        help_text="If this box is checked, your profile and content will not appear in the Hall of Fame or "
                  "'Community' feeds for new Gifts, Contractors, and Journals. Players who do not share a playgroup "
                  "with you will be unable to view your profile.")


class EmailSettingsForm(forms.Form):
    contract_invitations = forms.BooleanField(required=False)
    contract_updates = forms.BooleanField(required=False,
                                          help_text="Email when a Contract of interest changes its scheduled start "
                                                    "time or is canceled or when one I am attending ends and rewards are granted.")
    direct_messages = forms.BooleanField(required=False)
    intro_contracts = forms.BooleanField(required=False, widget=forms.HiddenInput)
    site_announcements = forms.BooleanField(required=False, widget=forms.HiddenInput)


class AcceptTermsForm(forms.Form):
    pass