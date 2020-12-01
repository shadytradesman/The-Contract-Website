from django import forms

from .models import ACTIVATION_STYLE, HIGH_ROLLER_STATUS, Enhancement, Drawback, CREATION_REASON, Power_Full, PowerTag

def set_field_html_name(cls, new_name):
    """
    This creates wrapper around the normal widget rendering,
    allowing for a custom field name (new_name).
    """
    old_render = cls.widget.render
    def _widget_render_wrapper(name=None, attrs=None, *args, **kwargs):
        new_attrs = None
        if type(cls.widget) is forms.widgets.Select:
            new_attrs = {"class": "form-control"}
        attrs = {**(attrs or {}), **(new_attrs or {})}
        return old_render(new_name, attrs=attrs, *args, **kwargs)

    cls.widget.render = _widget_render_wrapper

class EnhancementDrawbackPickerForm(forms.ModelForm):
    # used in the admin app for base_power
    def  __init__(self, *args, **kwargs):
        super(EnhancementDrawbackPickerForm, self).__init__(*args, **kwargs)
        self.fields['enhancements'].queryset = Enhancement.objects.order_by("-is_general").all()
        self.fields['drawbacks'].queryset = Drawback.objects.order_by("-is_general").all()


class TagPickerForm(forms.ModelForm):
    # used in the admin app for PremadeCategory
    def  __init__(self, *args, **kwargs):
        super(TagPickerForm, self).__init__(*args, **kwargs)
        self.fields['tags'].queryset = PowerTag.objects.order_by("tag").all()

class DrawbackModelForm(forms.ModelForm):
    class Meta:
        model = Drawback
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.fields['drawbacks'].queryset = Drawback.objects.order_by("is_general").all()

def make_enhancement_form(enhancement, enhancement_instance=None):
    class EnhancementForm(forms.Form):
        def get_label(enhancement):
            requirements = ""
            required_status = {}
            for status in HIGH_ROLLER_STATUS: required_status[status[0]] = status[1]
            if enhancement.required_status in [HIGH_ROLLER_STATUS[3][0], HIGH_ROLLER_STATUS[4][0]]:
                requirements = "requires: {}".format(required_status[enhancement.required_status])
            return '{} ({}) {}'.format(enhancement.name, enhancement.description, requirements)

        label= get_label(enhancement)
        enhancement_slug=str(enhancement.slug)
        eratta = enhancement.eratta
        multiplicity_allowed=enhancement.multiplicity_allowed
        is_selected = forms.BooleanField(required=True,
                                         label=label,
                                         widget=forms.CheckboxInput(attrs={'data-name': enhancement.name}))
        form_name = enhancement.form_name()
        if enhancement_instance:
            is_selected.initial=True
        set_field_html_name(is_selected, form_name)
        if enhancement.detail_field_label is not "" and enhancement.detail_field_label is not None:
            detail_text = forms.CharField(required=False,
                                          label=enhancement.detail_field_label,
                                          widget=forms.TextInput(attrs={'class': 'form-control css-detail-field'}))
            set_field_html_name(detail_text, enhancement.form_detail_name())
            if enhancement_instance:
                detail_text.initial=enhancement_instance.detail

    return EnhancementForm

def make_drawback_form(drawback):
    class DrawbackForm(forms.Form):
        def get_label(drawback):
            requirements = ""
            required_status = {}
            for status in HIGH_ROLLER_STATUS: required_status[status[0]] = status[1]
            if drawback.required_status in [HIGH_ROLLER_STATUS[3][0], HIGH_ROLLER_STATUS[4][0]]:
                requirements = "requires: {}".format(required_status[drawback.required_status])
            return '{} ({}) {}'.format(drawback.name, drawback.description, requirements)

        label= get_label(drawback)
        eratta = drawback.eratta
        drawback_slug=str(drawback.slug)
        multiplicity_allowed=drawback.multiplicity_allowed
        is_selected = forms.BooleanField(required=True,
                                         label=label,
                                         widget=forms.CheckboxInput(attrs={'data-name': drawback.name}))
        set_field_html_name(is_selected, drawback.form_name())
        if drawback.detail_field_label is not "" and drawback.detail_field_label is not None:
            detail_text = forms.CharField(required=False,
                                          label=drawback.detail_field_label,
                                          widget=forms.TextInput(attrs={'class': 'form-control css-detail-field'}))
            set_field_html_name(detail_text, drawback.form_detail_name())

    return DrawbackForm

def make_parameter_form(power_param):
    parameter = power_param.relevant_parameter
    class ParameterForm(forms.Form):
        param_choices = []
        for i in range(parameter.get_max_level()):
            param_choices.append((i, str(parameter.get_value_for_level(i) + power_param.get_status_tag(i))))
        label = parameter.name
        level_picker = forms.ChoiceField(choices=param_choices,
                                         initial=power_param.default)
        set_field_html_name(level_picker, parameter.slug)
    return ParameterForm

class CreatePowerForm(forms.Form):
    power_name = forms.CharField(label='Power Name', max_length=100)
    flavor = forms.CharField(label='Flavor Text',
                             widget=forms.Textarea,
                             help_text='A snippet of text that introduces the power in a flavorful way')
    description = forms.CharField(label='Description',
                                  widget=forms.Textarea,
                                  help_text='Describe what the power looks like when it is used, how it works, '
                                            'and its impact on the owner, target, and environment. All Powers '
                                            'are obviously supernatural unless stated otherwise.')
    system = forms.CharField(label='System', widget=forms.Textarea,
                             help_text='Describe this Power\'s cost, associated roll(s), conditions, and determination of outcome. '
                                       'You can reference the value of a Parameter by typing its name in lowercase, '
                                       'surrounded by double brackets, with spaces replaced by hyphens. For example, to display the value '
                                       'of a Power\'s "Cast Time" Parameter, write "[[cast-time]]".')
    activation_style = forms.ChoiceField(choices=ACTIVATION_STYLE, disabled=True)
    tags = forms.ModelMultipleChoiceField(queryset=PowerTag.objects.order_by("tag").all(),
                                          required=False,
                                          widget=forms.CheckboxSelectMultiple)
    example_description = forms.CharField(label='Example Description',
                                          widget=forms.Textarea,
                                          required=False,
                                          help_text='Admin only, optional, for the stock powers page. Follow-up advice for this power. '
                                                    'What sorts of Enhancements and Drawbacks would be good?')


    def __init__(self, base_power, *args, **kwargs):
        super(CreatePowerForm, self).__init__(*args, **kwargs)
        #
        # base_power context sensitive field mutations go here.
        #
        self.fields['activation_style'].help_text='Choose whether the power is always on (passive) or activated manually (active). ' \
                                                  'Default is ' + base_power.default_activation_style + "."
        self.fields['activation_style'].initial=base_power.default_activation_style

class DeletePowerForm(forms.Form):
    pass