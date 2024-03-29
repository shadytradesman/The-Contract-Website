from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from tinymce.widgets import TinyMCE

GUIDE_SECTION_TINYMCE_SETTINGS = {
    "theme": "silver",
    "height": 500,
    "menubar": False,
    "browser_spellcheck": True,
    "contextmenu": "useBrowserSpellcheck",
    "plugins": "advlist,autolink,lists,link,image,charmap,print,preview,anchor,"
               "searchreplace,visualblocks,code,fullscreen,insertdatetime,media,table,paste,"
               "code,help,wordcount",
    "toolbar": "formatselect fontselect fontsizeselect | "
               "bold italic strikethrough underline removeformat | backcolor forecolor | alignleft aligncenter "
               "| bullist numlist link unlink | table | image"
               " | help ",
    "toolbar_mode": 'wrap',
    'content_css': "/static/css/site.css",
}


class GuidebookForm(forms.Form):
    title = forms.CharField(label='Guidebook Title',
                            required=True,
                            max_length=380)
    content = forms.CharField(label='Content',
                              widget=TinyMCE(attrs={'cols': 80, 'rows': 30}, mce_attrs=GUIDE_SECTION_TINYMCE_SETTINGS),
                              max_length=73000,
                              required=False,
                              help_text='write the content for the guidebook intro.')


def make_guide_section_form(previous_section=None, next_section=None):
    prev_sect_pos = "Previous section ({}) Position: {}. ".format(previous_section.title, previous_section.position) if previous_section else ""
    next_sect_pos = "Next section ({}) Position: {}.".format(next_section.title, next_section.position) if next_section else ""
    position_help_text = "{}{}".format(prev_sect_pos, next_sect_pos)

    prev_sect_header = "Previous section ({}) Header level: {}. ".format(previous_section.title, previous_section.header_level) if previous_section else ""
    next_sect_header = "Next section ({}) Header level: {}. ".format(next_section.title, next_section.header_level) if next_section else ""
    header_help_text = "{}{}If this section's header level is greater than the previous, it is a child.".format(prev_sect_header, next_sect_header)
    class GuideSectionForm(forms.Form):
        title = forms.CharField(label='Section Title',
                                required=True,
                                max_length=380)
        slug = forms.SlugField(label='Slug',
                                required=True,
                                max_length=80)
        position = forms.IntegerField(initial=0,
                                      validators=[MinValueValidator(1)],
                                      help_text=position_help_text)
        header_level = forms.IntegerField(initial=1,
                                          validators=[MaxValueValidator(6), MinValueValidator(1)],
                                          help_text=header_help_text)
        is_hidden = forms.BooleanField(label='Hide from non-admins?',
                                       help_text="If checked, non-admins will not be able to view this article. Great for WIPs!",
                                       required=False)
        is_spoilers = forms.BooleanField(label='Contains spoilers??',
                                       help_text="If checked, users must opt-in to view this content.",
                                       required=False)
        content = forms.CharField(label='Content',
                                  widget=TinyMCE(attrs={'cols': 80, 'rows': 30}, mce_attrs=GUIDE_SECTION_TINYMCE_SETTINGS),
                                  max_length=73000,
                                  required=False,
                                  help_text='write the content for the section.')

        tags = forms.JSONField(label='tags',
                              required=False,
                               widget=forms.TextInput,
                              help_text='["tags", "for searching in", "navbar"]')
    return GuideSectionForm


class DeleteGuideSectionForm(forms.Form):
    pass