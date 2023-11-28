from django import forms
from .models import PrivateUserImage


def make_image_deletion_form(queryset):
    if queryset.model is PrivateUserImage:
        class ImageDeletionForm(forms.Form):
            #TODO: multi-select for deleting exiting images
            pass
    else:
        raise ValueError("Improper model type of queryset. supplied: {}".format(str(queryset.model)))


class ImageUploadForm(forms.Form):
    file = forms.FileField(label="Upload new image")