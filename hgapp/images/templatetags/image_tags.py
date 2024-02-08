from django import template

register = template.Library()


@register.inclusion_tag('images/image_thumb.html', takes_context=True)
def image_thumb(context, image, reportable=True):
    new_context = context
    new_context["image"] = image
    new_context["reportable"] = reportable
    return new_context
