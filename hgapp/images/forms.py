from django import forms

class ImageUploadForm(forms.Form):
    file = forms.FileField(label="Upload new image")