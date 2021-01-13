from django import forms
import account.forms
from django.conf import settings

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