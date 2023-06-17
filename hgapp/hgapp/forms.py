from django import forms
import account.forms
from account.models import EmailAddress
from collections import OrderedDict
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from hgapp.utilities import get_object_or_none

from info.terms import TERMS, EULA, PRIVACY

class SignupForm(account.forms.SignupForm):
    agree_to_tos = forms.BooleanField(required=True)
    terms=TERMS
    eula=EULA
    privacy=PRIVACY
    timezone = forms.ChoiceField(
        label=("My Timezone"),
        choices=settings.ACCOUNT_TIMEZONES,
        required=False,
        initial="US/Pacific"
    )

class ResendEmailConfirmation(forms.Form):
    pass

class LoginUsernameOrEmailForm(account.forms.LoginForm):

    username_or_email = forms.CharField(label= _("Username or Email"), max_length=100)
    authentication_fail_message = _("The username, email, and/or password you specified are not correct.")
    identifier_field = "username"

    def __init__(self, *args, **kwargs):
        super(LoginUsernameOrEmailForm, self).__init__(*args, **kwargs)
        field_order = ["username_or_email", "password", "remember"]
        if hasattr(self.fields, "keyOrder"):
            self.fields.keyOrder = field_order
        else:
            self.fields = OrderedDict((k, self.fields[k]) for k in field_order)

    def user_credentials(self):
        identifier = self.cleaned_data["username_or_email"]
        if "@" in identifier:
            email = get_object_or_none(EmailAddress.objects.filter(email=identifier, primary=True))
            if email is None:
                identifier = ""
            else:
                identifier = email.user.username
        return {
            "username": identifier,
            "password": self.cleaned_data["password"],
        }
