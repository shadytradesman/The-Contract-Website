from django.forms import ModelForm, ChoiceField
from .models import Report, MODERATION_ACTION
from django.utils.translation import ugettext_lazy as _


class ReportForm(ModelForm):
    class Meta:
        model = Report
        fields = ('reason', 'extended_reason')
        required = ('reason',)


class ModerationActionForm(ModelForm):
    class Meta:
        model = Report
        fields = ('moderation_reason', 'moderator_feedback')
        help_texts = {
            'moderation_reason': _('Actual reason for moderation'),
            'moderator_feedback': _('Deliver a personalized message to the poster'),
        }

    moderation_action = ChoiceField(choices=MODERATION_ACTION,
                                    required=True,
                                    help_text="Ban if you don't they're interested / able to reform, or if they're posting illegal shit.")

