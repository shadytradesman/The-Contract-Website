from django import forms
import account.forms
from info.terms import TERMS, EULA, PRIVACY
class SignupForm(account.forms.SignupForm):
    agree_to_tos = forms.BooleanField(required=True)
    terms=TERMS
    eula=EULA
    privacy=PRIVACY