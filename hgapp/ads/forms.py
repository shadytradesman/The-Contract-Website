from django import forms
from django.forms import ModelForm
from tinymce.widgets import TinyMCE

from .models import FakeAd


class AdForm(ModelForm):
    class Meta:
        model = FakeAd
        fields = ('headline', 'content')
        required = ('content', 'headline')
        widgets = {
            'content': TinyMCE(attrs={'cols': 70, 'rows': 10}),
        }
