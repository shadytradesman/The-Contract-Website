from django import forms

from tinymce.widgets import TinyMCE

GUIDE_SECTION_TINYMCE_SETTINGS = {
    "theme": "silver",
    "height": 500,
    "menubar": False,
    "plugins": "advlist,autolink,lists,link,image,charmap,print,preview,anchor,"
               "searchreplace,visualblocks,code,fullscreen,insertdatetime,media,table,paste,"
               "code,help,wordcount",
    "toolbar": "formatselect fontselect fontsizeselect | "
               "bold italic strikethrough underline removeformat | backcolor forecolor | alignleft aligncenter "
               "| bullist numlist link unlink | image "
               " | help",
    "toolbar_mode": 'wrap',
    'content_css': "/static/css/site.css",
}
class GuideSectionForm(forms.Form):
    title = forms.CharField(label='Section Title',
                            required=False,
                            max_length=380)
    content = forms.CharField(label='Content',
                              widget=TinyMCE(attrs={'cols': 80, 'rows': 30}, mce_attrs=GUIDE_SECTION_TINYMCE_SETTINGS),
                              max_length=73000,
                              required=False,
                              help_text='write the content for the section.')
