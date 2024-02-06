from django import template
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from reporting.models import Report, ALLOWED_CONTENT_APPS, ALLOWED_CONTENT_MODELS
from reporting.utilities import get_url_for_content, ensure_content_type_is_reportable, ensure_content_object_is_reportable

register = template.Library()


@register.inclusion_tag('reporting/report_button_snippet.html', takes_context=True)
def report_content_button(context, content):
    request = context["request"] if "request" in context else None
    if request is None:
        return {"empty": True}

    ensure_content_object_is_reportable(content_object=content)

    content_type = ContentType.objects.get_for_model(content)
    ensure_content_type_is_reportable(content_type=content_type)

    existing_report = None
    if not request.user.is_anonymous:
        existing_report = Report.objects.filter(reporting_user=request.user, url=get_url_for_content(content, content_type=content_type)).first()
    primary_url = reverse("reporting:report_content", args=(
                          content_type.app_label,
                          content_type.model,
                          content.pk,))
    url = "{}?next={}".format(primary_url, request.path)
    return {
        "url": url,
        "existing_report": existing_report,
    }
