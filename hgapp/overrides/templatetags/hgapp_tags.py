from django import template

register = template.Library()

@register.inclusion_tag('tags/gwynn_art.html')
def gwynn_art(filename):
    return {
        'filename': filename,
    }
